from dataclasses import dataclass, field
from typing import Dict, List, Optional

import torch


def _pick_device(device: Optional[str] = None) -> torch.device:
    if device:
        return torch.device(device)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _as_label_matrix(labels: torch.Tensor) -> torch.Tensor:
    """
    Convert labels to [n, c] multi-hot float tensor.

    Supported inputs:
    - [n] class ids
    - [n, c] multi-hot
    - [c, n] multi-hot (will be transposed)
    """
    if labels.ndim == 1:
        y = labels.to(torch.long)
        c = int(y.max().item()) + 1 if y.numel() > 0 else 0
        out = torch.zeros((y.shape[0], c), dtype=torch.float32, device=labels.device)
        if y.numel() > 0:
            out[torch.arange(y.shape[0], device=labels.device), y] = 1.0
        return out

    if labels.ndim != 2:
        raise ValueError("labels must be 1D class ids or 2D multi-hot matrix.")

    x = labels.to(torch.float32)
    # Heuristic: [c, n] if rows << cols and values are in {0,1}.
    if x.shape[0] < x.shape[1]:
        uniq = torch.unique(x)
        if torch.all((uniq == 0) | (uniq == 1)):
            return x.T.contiguous()
    return x.contiguous()


def _sign_pm1(x: torch.Tensor) -> torch.Tensor:
    out = torch.sign(x)
    out[out == 0] = 1
    return out


def _pairwise_similarity(label_mat: torch.Tensor) -> torch.Tensor:
    # S_{ij}=1 if share at least one label, else -1.
    shared = (label_mat @ label_mat.T) > 0
    return shared.to(torch.float32) * 2.0 - 1.0


def _normalize_rows_l2(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    return x / (x.norm(dim=1, keepdim=True) + eps)


@dataclass
class FCMHConfig:
    hash_bits: int = 64
    alpha_1: float = 1.0
    alpha_2: float = 1.0
    beta_1: float = 1.0
    beta_2: float = 1.0
    gamma: float = 1e-3
    lambda_reg: float = 1e-3
    m_groups: int = 4
    n_iter: int = 8
    seed: int = 42
    dtype: torch.dtype = torch.float32
    device: Optional[str] = None
    # Backward-compatible aliases.
    alpha_global: Optional[float] = None
    alpha_local: Optional[float] = None
    beta_label: Optional[float] = None
    gamma_p: Optional[float] = None
    ridge: Optional[float] = None
    local_groups: Optional[int] = None

    def __post_init__(self) -> None:
        if self.alpha_global is not None:
            self.alpha_1 = self.alpha_global
        if self.alpha_local is not None:
            self.alpha_2 = self.alpha_local
        if self.beta_label is not None:
            self.beta_1 = self.beta_label
            self.beta_2 = 0.0
        if self.gamma_p is not None:
            self.gamma = self.gamma_p
        if self.ridge is not None:
            self.lambda_reg = self.ridge
        if self.local_groups is not None:
            self.m_groups = self.local_groups


class FCMHEngine:
    """
    A practical PyTorch implementation of FCMH-style two-stage training:
    1) Learn shared binary codes B with global/local similarity + label regression.
    2) Learn modality projections W1/W2 by ridge regression onto B.
    """

    def __init__(self, config: FCMHConfig):
        self.cfg = config
        self.device = _pick_device(config.device)
        self.dtype = config.dtype
        self._rng = torch.Generator(device="cpu")
        self._rng.manual_seed(config.seed)

    def _build_local_similarity(self, labels_n_c: torch.Tensor) -> torch.Tensor:
        n = labels_n_c.shape[0]
        g = max(1, min(self.cfg.m_groups, n))
        if n == 0:
            return torch.empty((0, 0), device=self.device, dtype=self.dtype)
        # Deterministic chunk partition to mimic local neighborhoods.
        idx = torch.arange(n, device=self.device)
        chunks = torch.chunk(idx, g)
        s_local = torch.zeros((n, n), device=self.device, dtype=self.dtype)
        for ch in chunks:
            if ch.numel() == 0:
                continue
            lq = labels_n_c[ch]
            sq = _pairwise_similarity(lq).to(device=self.device, dtype=self.dtype)
            s_local[ch.unsqueeze(1), ch.unsqueeze(0)] = sq
        return s_local

    def fit(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor,
        labels: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            x1: image features [n, d1]
            x2: text features [n, d2]
            labels: [n], [n,c], or [c,n]
        Returns:
            dict with learned B, W1, W2, and S.
        """
        x1 = x1.to(device=self.device, dtype=self.dtype)
        x2 = x2.to(device=self.device, dtype=self.dtype)
        if x1.ndim != 2 or x2.ndim != 2:
            raise ValueError("x1 and x2 must be 2D tensors [n, d].")
        if x1.shape[0] != x2.shape[0]:
            raise ValueError("x1 and x2 must have the same sample size.")
        n = x1.shape[0]
        if n == 0:
            raise ValueError("empty batch is not allowed.")

        l_n_c = _as_label_matrix(labels).to(device=self.device, dtype=self.dtype)
        # Accept both [n, c] and [c, n] shaped labels; normalize to [n, c].
        if l_n_c.shape[0] != n and l_n_c.ndim == 2 and l_n_c.shape[1] == n:
            l_n_c = l_n_c.T.contiguous()
        if l_n_c.shape[0] != n:
            raise ValueError("labels sample count mismatch with x1/x2.")
        l_n_c = (l_n_c > 0).to(self.dtype)
        l_n_c_norm = _normalize_rows_l2(l_n_c)

        s_global = _pairwise_similarity(l_n_c_norm).to(device=self.device, dtype=self.dtype)
        s_local = self._build_local_similarity(l_n_c_norm)
        s = self.cfg.alpha_1 * s_global + self.cfg.alpha_2 * s_local

        r = self.cfg.hash_bits
        b = torch.randint(0, 2, (n, r), generator=self._rng, dtype=torch.int64)
        b = b.to(device=self.device, dtype=self.dtype) * 2.0 - 1.0

        for _ in range(self.cfg.n_iter):
            bt_b = b.T @ b
            reg_eye = self.cfg.gamma * torch.eye(r, device=self.device, dtype=self.dtype)
            # P: [c, r], solve (B^T B + gamma I) * P^T = B^T L
            p_t = torch.linalg.solve(bt_b + reg_eye, b.T @ l_n_c)
            p = p_t.T

            # Discrete-style update.
            affinity_term = s @ b
            label_term = l_n_c @ p
            # beta_1 and beta_2 jointly control label-guided term strength.
            b = _sign_pm1(affinity_term + (self.cfg.beta_1 + self.cfg.beta_2) * label_term)

        d1 = x1.shape[1]
        d2 = x2.shape[1]
        i1 = self.cfg.lambda_reg * torch.eye(d1, device=self.device, dtype=self.dtype)
        i2 = self.cfg.lambda_reg * torch.eye(d2, device=self.device, dtype=self.dtype)
        w1 = torch.linalg.solve(x1.T @ x1 + i1, x1.T @ b)  # [d1, r]
        w2 = torch.linalg.solve(x2.T @ x2 + i2, x2.T @ b)  # [d2, r]

        return {"B": b, "W1": w1, "W2": w2, "S": s}

    @staticmethod
    def encode(x: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
        return _sign_pm1(x @ w)


@dataclass
class MIHTable:
    w1: torch.Tensor
    w2: torch.Tensor
    v1: float
    v2: float
    table_weight: float


@dataclass
class MIHConfig:
    hash_bits: int = 64
    max_tables: int = 5
    topk_default: int = 100
    fcmh: FCMHConfig = field(default_factory=FCMHConfig)
    device: Optional[str] = None
    dtype: torch.dtype = torch.float32


class MIHEngine:
    """
    Multi-table Incremental Hashing (MIH) for cross-modal retrieval.

    - Each incoming batch trains one new FCMH hash table.
    - Per-table modal weights are computed by Eq.(4-10).
    - Keep at most K tables by removing the minimum table_weight.
    - Retrieval uses table modal weights + query-adaptive bit weights.
    """

    def __init__(self, config: MIHConfig):
        if config.hash_bits <= 0:
            raise ValueError("hash_bits must be positive.")
        if config.max_tables <= 0:
            raise ValueError("max_tables must be positive.")

        self.cfg = config
        self.device = _pick_device(config.device or config.fcmh.device)
        self.dtype = config.dtype

        # Ensure FCMH hash bits aligns with MIH.
        self._fcmh_cfg = FCMHConfig(**{**config.fcmh.__dict__, "hash_bits": config.hash_bits, "device": str(self.device)})
        self._fcmh = FCMHEngine(self._fcmh_cfg)

        self.tables: List[MIHTable] = []
        self._db_codes_pm1 = torch.empty((0, self.cfg.hash_bits), dtype=self.dtype, device=self.device)
        self._db_ids = torch.empty((0,), dtype=torch.long, device=self.device)
        self._next_id = 0

    @staticmethod
    def _modal_weight(
        b_modal: torch.Tensor,
        b_ref: torch.Tensor,
        s: torch.Tensor,
    ) -> float:
        # Ham_i = 0.5 * (r - B_i' B^T)
        r = b_ref.shape[1]
        ham = 0.5 * (r - (b_modal @ b_ref.T))
        raw = torch.sum(s * ham).item()

        s_pos = float((s == 1).sum().item())
        s_neg = float((s == -1).sum().item())
        v_min = -r * s_neg
        v_max = r * s_pos
        if v_max <= v_min:
            return 0.5
        v = (raw - v_min) / (v_max - v_min)
        return float(max(0.0, min(1.0, v)))

    def _append_to_db(self, b_pm1: torch.Tensor, ids: Optional[torch.Tensor]) -> None:
        n = b_pm1.shape[0]
        if ids is None:
            ids_new = torch.arange(self._next_id, self._next_id + n, device=self.device, dtype=torch.long)
        else:
            if ids.ndim != 1 or ids.shape[0] != n:
                raise ValueError("ids must be 1D and match batch size.")
            ids_new = ids.to(device=self.device, dtype=torch.long)
        self._db_codes_pm1 = torch.cat([self._db_codes_pm1, b_pm1], dim=0)
        self._db_ids = torch.cat([self._db_ids, ids_new], dim=0)
        self._next_id = max(self._next_id, int(ids_new.max().item()) + 1)

    def fit_batch(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor,
        labels: torch.Tensor,
        ids: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Train one new table from current batch and update MIH table pool.
        """
        ret = self._fcmh.fit(x1, x2, labels)
        b = ret["B"]
        w1 = ret["W1"]
        w2 = ret["W2"]
        s = ret["S"]

        x1d = x1.to(device=self.device, dtype=self.dtype)
        x2d = x2.to(device=self.device, dtype=self.dtype)
        b1 = FCMHEngine.encode(x1d, w1)
        b2 = FCMHEngine.encode(x2d, w2)

        v1 = self._modal_weight(b1, b, s)
        v2 = self._modal_weight(b2, b, s)
        table_w = (v1 + v2) * 0.5

        self.tables.append(MIHTable(w1=w1, w2=w2, v1=v1, v2=v2, table_weight=table_w))
        if len(self.tables) > self.cfg.max_tables:
            drop_idx = min(range(len(self.tables)), key=lambda i: self.tables[i].table_weight)
            self.tables.pop(drop_idx)

        self._append_to_db(b, ids)

        return {
            "B": b,
            "W1": w1,
            "W2": w2,
            "S": s,
            "v1": torch.tensor(v1, device=self.device, dtype=self.dtype),
            "v2": torch.tensor(v2, device=self.device, dtype=self.dtype),
            "table_weight": torch.tensor(table_w, device=self.device, dtype=self.dtype),
            "num_tables": torch.tensor(len(self.tables), device=self.device, dtype=torch.long),
        }

    @staticmethod
    def _query_adaptive_weights(xq: torch.Tensor, w: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
        """
        alpha_j = norm( (xq dot w_j) / ||w_j|| ) in [0,1], per query-bit.
        Input:
            xq: [nq, d]
            w: [d, r]
        Return:
            alpha: [nq, r]
        """
        w_norm = w.norm(dim=0, keepdim=True) + eps
        dist = (xq @ w) / w_norm
        d_min = dist.min(dim=1, keepdim=True).values
        d_max = dist.max(dim=1, keepdim=True).values
        alpha = (dist - d_min) / (d_max - d_min + eps)
        return alpha

    def _weighted_hamming_for_table(
        self,
        q_pm1: torch.Tensor,
        alpha: torch.Tensor,
    ) -> torch.Tensor:
        """
        Weighted Hamming between queries and DB for one table.
        q_pm1: [nq, r], alpha: [nq, r], db: [ndb, r]
        return: [nq, ndb]
        """
        xor = (q_pm1.unsqueeze(1) != self._db_codes_pm1.unsqueeze(0)).to(self.dtype)
        return (xor * alpha.unsqueeze(1)).sum(dim=2)

    def search(
        self,
        query: torch.Tensor,
        query_modality: str,
        topk: Optional[int] = None,
    ) -> Dict[str, torch.Tensor]:
        if len(self.tables) == 0:
            raise RuntimeError("No hash table available. Call fit_batch first.")
        if self._db_codes_pm1.shape[0] == 0:
            raise RuntimeError("Database is empty.")
        if query_modality not in ("image", "text"):
            raise ValueError("query_modality must be 'image' or 'text'.")

        q = query.to(device=self.device, dtype=self.dtype)
        if q.ndim != 2:
            raise ValueError("query must be [nq, d].")
        nq = q.shape[0]
        ndb = self._db_codes_pm1.shape[0]
        k = topk if topk is not None else self.cfg.topk_default
        if k <= 0:
            raise ValueError("topk must be positive.")
        k = min(k, ndb)

        total_dist = torch.zeros((nq, ndb), device=self.device, dtype=self.dtype)
        for t in self.tables:
            if query_modality == "image":
                w = t.w1
                vk = t.v1
            else:
                w = t.w2
                vk = t.v2
            q_code = _sign_pm1(q @ w)
            alpha = self._query_adaptive_weights(q, w)
            dist_k = self._weighted_hamming_for_table(q_code, alpha)
            total_dist += float(vk) * dist_k

        # deterministic tie-break: ids asc
        tie = self._db_ids.to(self.dtype).unsqueeze(0) * 1e-8
        score = total_dist + tie
        order = torch.argsort(score, dim=1, descending=False)
        top_idx = order[:, :k]
        out_ids = self._db_ids[top_idx]
        out_dist = torch.gather(total_dist, 1, top_idx)
        return {"ids": out_ids, "distances": out_dist}

    def clear(self) -> None:
        self.tables.clear()
        self._db_codes_pm1 = torch.empty((0, self.cfg.hash_bits), dtype=self.dtype, device=self.device)
        self._db_ids = torch.empty((0,), dtype=torch.long, device=self.device)
        self._next_id = 0

    def state_dict(self) -> Dict[str, object]:
        return {
            "num_tables": len(self.tables),
            "table_weights": [t.table_weight for t in self.tables],
            "modal_weights": [(t.v1, t.v2) for t in self.tables],
            "db_ids": self._db_ids.detach().clone(),
            "db_codes_pm1": self._db_codes_pm1.detach().clone(),
        }
