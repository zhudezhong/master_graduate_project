from io import BytesIO

import httpx
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18

from app.core.config import Settings
from app.schemas.ingest import ProductIngestRecord


class _TextEncoder(nn.Module):
    def __init__(self, out_dim: int, vocab_size: int = 50000, hidden_dim: int = 256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        layer = nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=8, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.proj = nn.Linear(hidden_dim, out_dim)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        x = self.embedding(token_ids)
        x = self.encoder(x)
        x = x.mean(dim=1)
        x = self.proj(x)
        return torch.nn.functional.normalize(x, dim=1)


class FeatureService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = torch.device(settings.device)
        self._build_models()

    def _build_models(self) -> None:
        try:
            weights = ResNet18_Weights.DEFAULT
            backbone = resnet18(weights=weights)
        except Exception:
            # Fallback to non-pretrained when weights are unavailable.
            backbone = resnet18(weights=None)
        backbone.fc = nn.Identity()
        self.image_encoder = backbone.to(self.device).eval()

        self.text_encoder = _TextEncoder(out_dim=self.settings.feature_dim_text).to(self.device).eval()
        self.image_transform = T.Compose(
            [
                T.Resize(256),
                T.CenterCrop(224),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    @staticmethod
    def _tokenize_text(text: str, max_len: int = 64, vocab_size: int = 50000) -> list[int]:
        text = (text or "").strip()
        if not text:
            return [1]
        ids = [abs(hash(ch)) % vocab_size for ch in text]
        if len(ids) > max_len:
            ids = ids[:max_len]
        return ids

    @staticmethod
    def _decode_image(content: bytes) -> Image.Image:
        try:
            return Image.open(BytesIO(content)).convert("RGB")
        except Exception:
            return Image.new("RGB", (224, 224), color=(128, 128, 128))

    def image_from_bytes(self, content: bytes, filename: str = "") -> torch.Tensor:
        del filename
        image = self._decode_image(content)
        x = self.image_transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feat = self.image_encoder(x)
        feat = torch.nn.functional.normalize(feat, dim=1)
        return feat.squeeze(0).to(torch.float32).cpu()

    def image_from_url(self, image_url: str) -> torch.Tensor:
        if not image_url:
            return self.image_from_bytes(b"", filename="empty")
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.get(image_url)
                resp.raise_for_status()
                return self.image_from_bytes(resp.content, filename=image_url)
        except Exception:
            return self.image_from_bytes(b"", filename=image_url)

    def text_from_query(self, text: str) -> torch.Tensor:
        token_ids = self._tokenize_text(text)
        x = torch.tensor([token_ids], dtype=torch.long, device=self.device)
        with torch.no_grad():
            feat = self.text_encoder(x)
        return feat.squeeze(0).to(torch.float32).cpu()

    def product_features(self, product: ProductIngestRecord) -> tuple[torch.Tensor, torch.Tensor]:
        image_feat = self.image_from_url(product.image_url or str(product.product_id))
        text_blob = f"{product.title}\n{product.description}\n{product.attributes}"
        text_feat = self.text_from_query(text_blob)
        return image_feat, text_feat
