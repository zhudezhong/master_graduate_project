from app.core.config import Settings
from app.infra.catalog import ProductCatalog
from app.infra.kafka_client import ProductQueue
from app.infra.milvus_client import MilvusRepository
from app.services.feature_service import FeatureService
from app.services.hash_service import HashEngineService
from app.services.ingest_service import IngestService
from app.services.retrieval_service import RetrievalService


class AppContainer:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.catalog = ProductCatalog()
        self.queue = ProductQueue(settings)
        self.feature_service = FeatureService(settings)
        self.hash_service = HashEngineService(settings)
        self.milvus_repo = MilvusRepository(settings)

        self.ingest_service = IngestService(
            queue=self.queue,
            catalog=self.catalog,
            feature_service=self.feature_service,
            hash_service=self.hash_service,
            milvus_repo=self.milvus_repo,
        )
        self.retrieval_service = RetrievalService(
            catalog=self.catalog,
            feature_service=self.feature_service,
            hash_service=self.hash_service,
            milvus_repo=self.milvus_repo,
        )
