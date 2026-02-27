from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch


def _pick_device(device: Optional[str] = None) -> torch.device:
    if device:
        return torch.device(device)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _next_power_of_two(n: int) -> int:
    n = max(1, n)
    return 1 << (n - 1).bit_length()


def _hadamard(order: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    # Sylvester construction, order must be power of two.
    if order < 1 or (order & (order - 1)) != 0:
        raise ValueError("Hadamard order must be a positive power of two.")
    h = torch.tensor([[1.0]], device=device, dtype=dtype)
    while h.shape[0] < order:
        h = torch.cat(
            (
                torch.cat((h, h), dim=1),
                torch.cat((h, -h), dim=1),
            ),
            dim=0,
        )
    return h


@dataclass
class SCPHConfig:
    hash_bits: int = 64
    alpha: float = 2.0
    beta: float = 1.0
    knn_k: int = 20
    ridge: float = 1e-4
    seed: int = 42
    dtype: torch.dtype = torch.float32
    device: Optional[str] = None


class SCPHEngine:
    """
    PyTorch implementation of SCPH algorithm engine.

    Core steps per time-batch:
    1) Assign/keep fixed concept code for each class from a Hadamard pool.
    2) Generate pseudo labels for unlabeled samples with KNN over labeled samples.
    3) Build concept reference matrix C and pairwise similarity matrix S.
    4) Solve projection matrix W in closed form:
       W = ( -a/2 * X^T S X + b * X^T X + lambda I )^{-1} X^T S C
    """

    def __init__(self, config: SCPHConfig):
        self.cfg = config
        self.device = _pick_device(config.device)
        self.dtype = config.dtype
        self._rng = torch.Generator(device="cpu")
        self._rng.manual_seed(config.seed)

        self.W: Optional[torch.Tensor] = None  # [d, r]
        self.W_history: List[torch.Tensor] = []

        self._hadamard_order = _next_power_of_two(config.hash_bits)
        self._code_pool = self._build_code_pool(self._hadamard_order)
        self._used_pool_indices: set[int] = set()
        self.class_to_code: Dict[int, torch.Tensor] = {}

    def _build_code_pool(self, order: int) -> List[torch.Tensor]:
        h = _hadamard(order, self.device, self.dtype)[:, : self.cfg.hash_bits]
        return [h[i].clone() for i in range(h.shape[0])]

    def _expand_code_pool_if_needed(self) -> None:
        if len(self._used_pool_indices) < len(self._code_pool):
            return
        new_order = self._hadamard_order * 2
        new_pool = self._build_code_pool(new_order)
        # Keep old codes unchanged; append only newly available rows.
        self._code_pool.extend(new_pool[self._hadamard_order :])
        self._hadamard_order = new_order

    def _assign_code_for_class(self, cls: int) -> None:
        if cls in self.class_to_code:
            return
        self._expand_code_pool_if_needed()
        available = [i for i in range(len(self._code_pool)) if i not in self._used_pool_indices]
        if not available:
            raise RuntimeError("No available concept code rows.")
        pick = available[torch.randint(0, len(available), (1,), generator=self._rng).item()]
        self._used_pool_indices.add(pick)
        self.class_to_code[cls] = self._code_pool[pick].clone()

    def _ensure_codes(self, labels: torch.Tensor) -> None:
        classes = torch.unique(labels).tolist()
        for c in classes:
            self._assign_code_for_class(int(c))

    def _pseudo_label_knn(self, x_u: torch.Tensor, x_l: torch.Tensor, y_l: torch.Tensor) -> torch.Tensor:
        if x_u.numel() == 0:
            return torch.empty((0,), dtype=torch.long, device=self.device)
        if x_l.numel() == 0:
            raise ValueError("Unlabeled samples exist but labeled samples are empty.")
        k = min(self.cfg.knn_k, x_l.shape[0])
        dist = torch.cdist(x_u, x_l, p=2)  # [nu, nl]
        nn_idx = torch.topk(dist, k=k, largest=False, dim=1).indices  # [nu, k]
        nn_labels = y_l[nn_idx]  # [nu, k]

        # Majority vote; ties broken by smallest class id.
        classes = torch.unique(y_l).sort().values
        votes = torch.stack([(nn_labels == c).sum(dim=1) for c in classes], dim=1)  # [nu, C]
        winners = votes.argmax(dim=1)
        return classes[winners]

    def _build_concept_matrix(self, labels: torch.Tensor) -> torch.Tensor:
        self._ensure_codes(labels)
        codes = [self.class_to_code[int(c.item())] for c in labels]
        return torch.stack(codes, dim=0)  # [n, r]

    @staticmethod
    def _build_similarity(labels: torch.Tensor) -> torch.Tensor:
        # +1 for similar (same label), -1 otherwise.
        sim = (labels.unsqueeze(1) == labels.unsqueeze(0)).to(torch.float32)
        return sim * 2.0 - 1.0  # [n, n]

    @staticmethod
    def _sign_binary(x: torch.Tensor) -> torch.Tensor:
        # Keep {-1, +1}; zero mapped to +1.
        out = torch.sign(x)
        out[out == 0] = 1
        return out

    def fit_batch(
        self,
        x_l: torch.Tensor,
        y_l: torch.Tensor,
        x_u: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Train/update SCPH for one arriving time-batch.

        Args:
            x_l: labeled features [n_l, d]
            y_l: labeled class ids [n_l]
            x_u: unlabeled features [n_u, d], optional
        Returns:
            dict containing W, labels, C, S, and batch hash codes.
        """
        x_l = x_l.to(device=self.device, dtype=self.dtype)
        y_l = y_l.to(device=self.device, dtype=torch.long)
        x_u = (
            x_u.to(device=self.device, dtype=self.dtype)
            if x_u is not None
            else torch.empty((0, x_l.shape[1]), device=self.device, dtype=self.dtype)
        )

        y_u = self._pseudo_label_knn(x_u, x_l, y_l) if x_u.shape[0] > 0 else torch.empty((0,), dtype=torch.long, device=self.device)

        X = torch.cat([x_l, x_u], dim=0)  # [n, d]
        y = torch.cat([y_l, y_u], dim=0)  # [n]
        if X.shape[0] == 0:
            raise ValueError("Empty batch is not allowed.")

        C = self._build_concept_matrix(y)  # [n, r]
        S = self._build_similarity(y).to(device=self.device, dtype=self.dtype)  # [n, n]

        XT = X.T  # [d, n]
        d = XT.shape[0]
        I = torch.eye(d, device=self.device, dtype=self.dtype)
        A = (-self.cfg.alpha / 2.0) * (XT @ S @ XT.T) + self.cfg.beta * (XT @ XT.T) + self.cfg.ridge * I
        B = XT @ S @ C
        W = torch.linalg.solve(A, B)  # [d, r]

        self.W = W
        self.W_history.append(W.detach().clone())

        H = self._sign_binary(X @ W)  # [n, r]
        return {
            "W": W,
            "labels": y,
            "labels_u": y_u,
            "C": C,
            "S": S,
            "H": H,
        }

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        if self.W is None:
            raise RuntimeError("Model has not been trained. Call fit_batch first.")
        x = x.to(device=self.device, dtype=self.dtype)
        return self._sign_binary(x @ self.W)

    def state_dict(self) -> Dict[str, object]:
        return {
            "W": self.W,
            "W_history": self.W_history,
            "class_to_code": {k: v.clone() for k, v in self.class_to_code.items()},
            "hadamard_order": self._hadamard_order,
            "used_pool_indices": list(self._used_pool_indices),
        }

if __name__ == "__main__":
    h_order = _next_power_of_two(64)
    h = _hadamard(h_order, torch.device("mps"), torch.float32)
    print(h.shape)
    print()
    print(h)