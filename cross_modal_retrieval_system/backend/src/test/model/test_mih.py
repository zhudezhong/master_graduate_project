from pathlib import Path
import sys

import pytest
import torch

# Ensure backend/src is importable when tests are run from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from model.mih import FCMHConfig, MIHConfig, MIHEngine


def _make_batch(n: int, d1: int, d2: int, n_classes: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    x1 = torch.randn(n, d1, dtype=torch.float32)
    x2 = torch.randn(n, d2, dtype=torch.float32)
    y = torch.randint(0, n_classes, (n,), dtype=torch.long)
    return x1, x2, y


def test_fit_batch_returns_expected_keys_and_shapes() -> None:
    torch.manual_seed(7)
    cfg = MIHConfig(
        hash_bits=16,
        max_tables=3,
        topk_default=5,
        fcmh=FCMHConfig(hash_bits=16, n_iter=3, m_groups=2, device="cpu"),
        device="cpu",
    )
    engine = MIHEngine(cfg)

    x1, x2, y = _make_batch(n=12, d1=8, d2=6, n_classes=4)
    out = engine.fit_batch(x1, x2, y)

    assert out["B"].shape == (12, 16)
    assert out["W1"].shape == (8, 16)
    assert out["W2"].shape == (6, 16)
    assert out["S"].shape == (12, 12)
    assert int(out["num_tables"].item()) == 1
    assert engine.state_dict()["num_tables"] == 1


def test_mih_keeps_max_tables_by_evicting_lowest_weight() -> None:
    torch.manual_seed(13)
    cfg = MIHConfig(
        hash_bits=12,
        max_tables=2,
        fcmh=FCMHConfig(hash_bits=12, n_iter=2, m_groups=2, device="cpu"),
        device="cpu",
    )
    engine = MIHEngine(cfg)

    for _ in range(3):
        x1, x2, y = _make_batch(n=10, d1=5, d2=7, n_classes=3)
        engine.fit_batch(x1, x2, y)

    state = engine.state_dict()
    assert state["num_tables"] == 2
    assert len(state["table_weights"]) == 2
    assert state["db_codes_pm1"].shape[0] == 30


def test_search_returns_sorted_topk_results() -> None:
    torch.manual_seed(23)
    cfg = MIHConfig(
        hash_bits=10,
        max_tables=2,
        topk_default=4,
        fcmh=FCMHConfig(hash_bits=10, n_iter=2, m_groups=2, device="cpu"),
        device="cpu",
    )
    engine = MIHEngine(cfg)

    x1, x2, y = _make_batch(n=14, d1=6, d2=9, n_classes=4)
    engine.fit_batch(x1, x2, y)

    q_img = torch.randn(3, 6, dtype=torch.float32)
    out = engine.search(q_img, query_modality="image", topk=4)
    assert out["ids"].shape == (3, 4)
    assert out["distances"].shape == (3, 4)
    assert torch.all(out["distances"][:, 1:] >= out["distances"][:, :-1])

    q_txt = torch.randn(2, 9, dtype=torch.float32)
    out_t = engine.search(q_txt, query_modality="text", topk=3)
    assert out_t["ids"].shape == (2, 3)


def test_search_rejects_invalid_query_modality() -> None:
    cfg = MIHConfig(
        hash_bits=8,
        max_tables=1,
        fcmh=FCMHConfig(hash_bits=8, n_iter=1, m_groups=1, device="cpu"),
        device="cpu",
    )
    engine = MIHEngine(cfg)
    x1, x2, y = _make_batch(n=6, d1=4, d2=4, n_classes=2)
    engine.fit_batch(x1, x2, y)

    with pytest.raises(ValueError, match="query_modality"):
        engine.search(torch.randn(1, 4), query_modality="audio", topk=2)
