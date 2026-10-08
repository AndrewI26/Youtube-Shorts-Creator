from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .database import make_engine, make_session_factory
from .routers import shorts


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # The schema is managed by Alembic: run `uv run alembic upgrade head`.
        settings.media_dir.mkdir(parents=True, exist_ok=True)
        yield
        engine.dispose()

    app = FastAPI(title="YouTube Shorts Creator", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(shorts.router)
    return app


app = create_app()
