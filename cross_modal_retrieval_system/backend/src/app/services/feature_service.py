from io import BytesIO
from pathlib import Path
import time

import httpx
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18
from transformers import AutoModel, AutoTokenizer

from app.core.config import Settings, settings
from app.schemas.ingest import ProductIngestRecord


class _TextEncoder(nn.Module):
    """
    Lightweight Chinese text encoder based on a pretrained embedding model.

    Uses a HuggingFace model to produce sentence embeddings and optionally
    projects them to the configured output dimension.
    """

    def __init__(self, model_name: str, out_dim: int, device: torch.device):
        super().__init__()
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.backbone = AutoModel.from_pretrained(model_name).to(device)
        hidden_size = int(self.backbone.config.hidden_size)
        if hidden_size == out_dim:
            self.proj = nn.Identity()
        else:
            self.proj = nn.Linear(hidden_size, out_dim).to(device)

    def forward(self, texts: list[str]) -> torch.Tensor:
        enc = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=64,
            return_tensors="pt",
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        with torch.no_grad():
            outputs = self.backbone(**enc)
            # Mean pooling over sequence length.
            pooled = outputs.last_hidden_state.mean(dim=1)
            x = self.proj(pooled)
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

        # Chinese text embedding model (lightweight, pretrained).
        # Hidden size is 768, matching default feature_dim_text.
        self.text_encoder = _TextEncoder(
            model_name=self.settings.text_model_name,
            out_dim=self.settings.feature_dim_text,
            device=self.device,
        ).eval()
        self.image_transform = T.Compose(
            [
                T.Resize(256),
                T.CenterCrop(224),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    @staticmethod
    def _decode_image(content: bytes) -> Image.Image:
        try:
            return Image.open(BytesIO(content)).convert("RGB")
        except Exception:
            return Image.new("RGB", (224, 224), color=(128, 128, 128))

    @staticmethod
    def _is_punish_payload(content: bytes) -> bool:
        # Anti-bot response from alicdn often returns JSON containing wait_h5.html.
        text = content[:1024].decode("utf-8", errors="ignore")
        return "wait_h5.html" in text or "\"rgv587_flag\"" in text

    def _download_image_bytes(self, image_url: str) -> bytes:
        primary_headers = {
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.taobao.com/",
        }
        fallback_headers = {"User-Agent": primary_headers["User-Agent"], "Accept": primary_headers["Accept"]}
        def content_to_image(content: bytes) -> Image.Image:
            image = Image.open(BytesIO(content)).convert("RGB")
            data_dir = Path(__file__).resolve().parents[3] / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            output_path = data_dir / f"fetched_{int(time.time() * 1000)}.jpg"
            image.save(output_path, format="JPEG")
            return image

        # trust_env=False avoids accidental proxy injection that may return non-image payloads.
        for headers in (primary_headers, fallback_headers):
            with httpx.Client(
                timeout=self.settings.request_timeout_seconds,
                follow_redirects=True,
                headers=headers,
                trust_env=False,
            ) as client:
                resp = client.get(image_url)
                resp.raise_for_status()
                content = resp.content
                content_type = (resp.headers.get("content-type") or "").lower()

                if self._is_punish_payload(content):
                    continue
                if content_type.startswith("image/"):
                    return content

        raise ValueError(f"failed to fetch valid image bytes from url: {image_url}")

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
            content = self._download_image_bytes(image_url)
            return self.image_from_bytes(content, filename=image_url)
        except Exception:
            return self.image_from_bytes(b"", filename=image_url)

    def text_from_query(self, text: str) -> torch.Tensor:
        text = (text or "").strip()
        if not text:
            text = "空查询"
        with torch.no_grad():
            feat = self.text_encoder([text])
        return feat.squeeze(0).to(torch.float32).cpu()

    def product_features(self, product: ProductIngestRecord) -> tuple[torch.Tensor, torch.Tensor]:
        image_feat = self.image_from_url(product.image_url)
        text_blob = f"{product.title}\n{product.description}\n{product.attributes}"
        text_feat = self.text_from_query(text_blob)
        return image_feat, text_feat


_feature_service_singleton: FeatureService | None = None


def get_feature_service_singleton() -> FeatureService:
    global _feature_service_singleton
    if _feature_service_singleton is None:
        _feature_service_singleton = FeatureService(settings)
    return _feature_service_singleton
