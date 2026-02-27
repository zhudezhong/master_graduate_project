from pathlib import Path
import sys

import pytest
import torch

# Ensure backend/src is importable when tests are run from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from model.scph import SCPHConfig, SCPHEngine, _hadamard, _next_power_of_two


def test_next_power_of_two_basic_cases() -> None:
    assert _next_power_of_two(0) == 1
    assert _next_power_of_two(1) == 1
    assert _next_power_of_two(3) == 4
    assert _next_power_of_two(64) == 64
    assert _next_power_of_two(65) == 128


def test_hadamard_properties_and_invalid_order() -> None:
    n = 8
    h = _hadamard(n, torch.device("cpu"), torch.float32)

    assert h.shape == (n, n)
    assert set(h.unique().tolist()) == {-1.0, 1.0}
    assert torch.allclose(h @ h.T, n * torch.eye(n), atol=1e-5)

    with pytest.raises(ValueError, match="positive power of two"):
        _hadamard(6, torch.device("cpu"), torch.float32)


def test_fit_batch_returns_expected_shapes_and_binary_hashes() -> None:
    engine = SCPHEngine(SCPHConfig(hash_bits=8, seed=123, device="cpu"))

    x_l = torch.tensor(
        [
            [0.0, 1.0, 2.0],
            [0.1, 0.9, 1.9],
            [3.0, 2.0, 1.0],
            [3.1, 2.1, 0.9],
        ],
        dtype=torch.float32,
    )
    y_l = torch.tensor([0, 0, 1, 1], dtype=torch.long)
    x_u = torch.tensor([[0.05, 0.95, 2.0], [3.05, 2.05, 1.0]], dtype=torch.float32)

    out = engine.fit_batch(x_l=x_l, y_l=y_l, x_u=x_u)

    n_total = x_l.shape[0] + x_u.shape[0]
    d = x_l.shape[1]
    r = engine.cfg.hash_bits

    assert out["W"].shape == (d, r)
    assert out["labels"].shape == (n_total,)
    assert out["labels_u"].shape == (x_u.shape[0],)
    assert out["C"].shape == (n_total, r)
    assert out["S"].shape == (n_total, n_total)
    assert out["H"].shape == (n_total, r)
    assert set(out["H"].unique().tolist()) <= {-1.0, 1.0}
    assert len(engine.W_history) == 1


def test_encode_requires_fit_first() -> None:
    engine = SCPHEngine(SCPHConfig(hash_bits=8, device="cpu"))
    with pytest.raises(RuntimeError, match="Model has not been trained"):
        engine.encode(torch.randn(2, 3))


def test_same_seed_gives_same_class_code_assignment() -> None:
    cfg = SCPHConfig(hash_bits=8, seed=7, device="cpu")
    e1 = SCPHEngine(cfg)
    e2 = SCPHEngine(cfg)
    labels = torch.tensor([0, 1, 2, 1, 0], dtype=torch.long)

    c1 = e1._build_concept_matrix(labels)
    c2 = e2._build_concept_matrix(labels)

    assert torch.equal(c1, c2)
