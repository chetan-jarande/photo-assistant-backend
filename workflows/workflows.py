from datetime import timedelta
from typing import List, Dict, Any

# from temporalio import workflow
from workflows.activities import (
    ingest_photo,
    generate_vector_batch,
    reverse_geocode_batch,
)


# Mock decorators
class workflow:
    @staticmethod
    def defn(cls):
        return cls

    @staticmethod
    def run(func):
        return func


@workflow.defn
class PhotoIngestionWorkflow:
    @workflow.run
    async def run(self, photo_paths: List[str]) -> Dict[str, Any]:
        """
        Orchestrate the ingestion of multiple photos.
        """
        results = []

        # In a real workflow, we would use workflow.execute_activity
        # results = await workflow.execute_activity(
        #     ingest_photo,
        #     photo_paths[0],
        #     start_to_close_timeout=timedelta(minutes=5)
        # )

        # Mock execution logic
        for path in photo_paths:
            # We can't really execute activities here without Temporal runtime
            # Just simulating the flow
            res = await ingest_photo(path)
            results.append(res)

        photo_ids = [r["id"] for r in results]

        # Parallel execution of enrichment tasks
        await generate_vector_batch(photo_ids)
        await reverse_geocode_batch(photo_ids)

        return {"status": "completed", "processed_count": len(photo_paths)}
