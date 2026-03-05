from dataclasses import dataclass

import torch

from app.core.config import Settings
from model.mih import FCMHConfig, MIHConfig, MIHEngine
from model.scph import SCPHConfig, SCPHEngine


def pm1_to_binary_vector(x: torch.Tensor) -> list[int]:
    bits = (x > 0).to(torch.uint8).tolist()
    return [int(v) for v in bits]


@dataclass
class HashUpdateResult:
    mode: str
    num_samples: int
    num_tables: int | None = None


class HashEngineService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.scph = SCPHEngine(SCPHConfig(hash_bits=settings.hash_bits, device=settings.device))
        self.mih = MIHEngine(
            MIHConfig(
                hash_bits=settings.hash_bits,
                max_tables=5,
                topk_default=settings.topk_default,
                fcmh=FCMHConfig(hash_bits=settings.hash_bits, device=settings.device),
                device=settings.device,
            )
        )

    def update_scph(self, image_feats: torch.Tensor, labels: torch.Tensor) -> HashUpdateResult:
        self.scph.fit_batch(x_l=image_feats, y_l=labels)
        return HashUpdateResult(mode="scph", num_samples=image_feats.shape[0])

    def update_mih(self, image_feats: torch.Tensor, text_feats: torch.Tensor, labels: torch.Tensor, ids: torch.Tensor) -> HashUpdateResult:
        ret = self.mih.fit_batch(x1=image_feats, x2=text_feats, labels=labels, ids=ids)
        return HashUpdateResult(
            mode="mih",
            num_samples=image_feats.shape[0],
            num_tables=int(ret["num_tables"].item()),
        )

    def encode_image_scph(self, image_feat: torch.Tensor) -> list[int]:
        x = image_feat.unsqueeze(0)
        code = self.scph.encode(x)[0]
        return pm1_to_binary_vector(code)

    def encode_mih_query(self, feature: torch.Tensor, modality: str, topk: int) -> dict[str, torch.Tensor]:
        q = feature.unsqueeze(0)
        return self.mih.search(q, query_modality=modality, topk=topk)
