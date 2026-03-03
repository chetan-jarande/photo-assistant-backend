from core.config import settings, Environments
from utils.logger import get_logger


logger = get_logger(__name__)


_llm_client_instance = None


def initialize_llm_client():
    """ "Initializes the global OpenAI client instance.
    Args:
        mode (str): "sync" for synchronous client, "async" for asynchronous client.
    """
    global _llm_client_instance
    _api_key = settings.LLM_API_KEY.get_secret_value() if settings.LLM_API_KEY else None

    if not _api_key:
        logger.error("OPENAI_API_KEY is not configured for OpenAI client initialization.")
        raise ValueError("OPENAI_API_KEY is required but not set for OpenAI client.")

    logger.info("Global LLM client instance initialized successfully.")


async def run_startup_logic():
    """
    Orchestrates all startup tasks.
    """
    logger.info("Executing application startup logic...")
    try:
        # Initialize the OpenAI API client
        initialize_llm_client()
        # TODO: Import DB connections here
        logger.info("LLM client initialized successfully.")
        # Any other startup tasks can be added here

        logger.info("All startup tasks completed.")
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to execute application startup logic. Application cannot start. Error: {e}",
            exc_info=True,
        )
        raise e


async def run_shutdown_logic():
    """
    Orchestrates all shutdown tasks.
    """
    logger.info("Executing application shutdown logic...")
    # Add any shutdown tasks here
    # TODO: Shutdown: Close database connection

    logger.info("All shutdown tasks completed.")
