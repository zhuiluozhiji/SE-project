from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok", "service": settings.project_name}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
