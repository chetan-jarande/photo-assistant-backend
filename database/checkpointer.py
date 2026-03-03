from typing import Any, AsyncIterator, Dict, Optional, Sequence, Tuple
import json
from langchain_core.runnables import RunnableConfig
from langchain_core.load import dumpd, load
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from database.surreal_client import surreal_client


class SurrealDBCheckpointer(BaseCheckpointSaver):
    """
    Custom Checkpointer that persists LangGraph state to SurrealDB.
    """

    def __init__(self, client=None):
        super().__init__()
        self.client = client or surreal_client.db

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        Get a checkpoint tuple from the database.
        """
        thread_id = config["configurable"].get("thread_id")
        if not thread_id:
            return None

        # Query the latest checkpoint for this thread
        # Assuming table `checkpoints` with `id` as thread_id (or composite)
        # For simplicity, we might store checkpoints as `checkpoints:<thread_id>:<checkpoint_id>`
        # But BaseCheckpointSaver usually manages `thread_id` and `checkpoint_id`.

        # Let's try to find the latest checkpoint for the thread
        query = f"SELECT * FROM checkpoints WHERE thread_id = '{thread_id}' ORDER BY ts DESC LIMIT 1"
        try:
            result = await self.client.query(query)
            if not result or not result[0]["result"]:
                return None

            record = result[0]["result"][0]
            # Deserialize using langchain_core.load
            checkpoint = load(json.loads(record["checkpoint"]))
            metadata = load(json.loads(record["metadata"]))
            parent_config = json.loads(record.get("parent_config", "{}"))

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
            )
        except Exception as e:
            print(f"Error getting checkpoint: {e}")
            return None

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """
        Save a checkpoint to the database.
        """
        thread_id = config["configurable"].get("thread_id")
        checkpoint_id = checkpoint["id"]

        # We need to serialize the checkpoint and metadata
        # Use langchain_core.load.dumpd to serialize LangChain objects

        # Create record
        record = {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint": json.dumps(dumpd(checkpoint)),
            "metadata": json.dumps(dumpd(metadata)),
            "ts": metadata.get("ts"),  # Timestamp
            "parent_config": json.dumps(config, default=str),
        }

        # Insert into SurrealDB
        # We use a unique ID for the record: checkpoints:thread_id:checkpoint_id
        record_id = f"checkpoints:{thread_id}_{checkpoint_id}"

        try:
            await self.client.create(record_id, record)
        except Exception as e:
            # If it exists, update it? Checkpoints are usually immutable.
            print(f"Error saving checkpoint: {e}")

        return config

    async def alist(
        self,
        config: RunnableConfig,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints."""
        # Implementation for listing history
        yield CheckpointTuple(config, {}, {}, {})  # Dummy yield

    # Sync methods are not implemented as we expect async usage
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        raise NotImplementedError("Use aget_tuple")

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        raise NotImplementedError("Use aput")

    def list(
        self,
        config: RunnableConfig,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Any:
        raise NotImplementedError("Use alist")
