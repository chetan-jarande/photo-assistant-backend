from surrealdb import Surreal
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class SurrealClient:
    def __init__(self):
        self.db = Surreal(settings.SURREALDB_URL)
        self.is_connected = False

    async def connect(self):
        """Establish connection to SurrealDB and sign in."""
        try:
            await self.db.connect()
            await self.db.signin({
                "user": settings.SURREALDB_USER,
                "pass": settings.SURREALDB_PASS
            })
            await self.db.use(namespace=settings.SURREALDB_NS, database=settings.SURREALDB_DB)
            self.is_connected = True
            logger.info("Successfully connected to SurrealDB")
        except Exception as e:
            logger.error(f"Failed to connect to SurrealDB: {e}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Close the database connection."""
        if self.is_connected:
            await self.db.close()
            self.is_connected = False
            logger.info("Disconnected from SurrealDB")

surreal_client = SurrealClient()
