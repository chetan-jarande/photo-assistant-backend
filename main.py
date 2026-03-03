import uvicorn

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from core.config import settings, Environments
from utils.logger import get_logger
from utils.init_helper import run_startup_logic, run_shutdown_logic

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events using helper functions.
    - Initializes resources on startup (before yield).
    - Cleans up resources on shutdown (after yield).
    """
    logger.info("Application lifespan: Initiating startup sequence...")
    try:
        logger.info(
            f"Application settings loaded successfully for project: {settings.PROJECT_NAME}",
            extra=settings.model_dump(),
        )
        await run_startup_logic()
        logger.info("Application lifespan: Startup sequence completed successfully.")
        # This is where the application will run until shutdown.
        # The application runs while the lifespan context manager is active
        yield
    except Exception as e:
        logger.exception(f"Application lifespan: CRITICAL error during startup: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Application failed to initialize critical services: {str(e)}",
        ) from e
    finally:
        # This block executes regardless of whether an exception occurred in the try block or during app execution.
        logger.info("Application lifespan: Initiating shutdown sequence...")
        await run_shutdown_logic()
        logger.info("Application lifespan: Shutdown sequence completed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def root(request: Request):
    return {
        "message": "Photography Assistant AI Backend is running",
        "status": "ok",
    }


# --- Health Check Endpoint ---
@app.get(
    "/status",
    description="Endpoint for Service Availability, including database connectivity.",
    tags=["Health Check"],
)
def service_status_check():
    """
    Provides the operational status of the service, including its
    ability to connect to the database.
    """
    response_content = {
        "status": "healthy",
        "database": "not connected",
    }

    return JSONResponse(content=response_content, status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    should_reload = settings.CONF_ENV == Environments.DEV
    port = settings.SERVER_PORT
    uvicorn.run(
        app="main:app",
        host=settings.SERVER_HOST,
        port=port,
        reload=should_reload,
        workers=1 if should_reload else 5,
    )
