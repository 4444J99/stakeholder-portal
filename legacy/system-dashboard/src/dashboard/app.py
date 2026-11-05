"""FastAPI application — system dashboard for the eight-organ system."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from organvm_engine.paths import PathConfig, resolve_path_config

from dashboard.routes import health, registry, graph, soak, essays, omega, progress, atoms, ecosystem, pulse, ontologia, content, testament, network, trivium, irf
from dashboard.routes import api_v1

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

def create_app(config: PathConfig | None = None) -> FastAPI:
    """Build the dashboard app with an explicit path configuration."""
    app = FastAPI(
        title="organvm system dashboard",
        description="Live health dashboard for the eight-organ system",
        version="0.1.0",
    )
    app.state.path_config = resolve_path_config(config)
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(health.router)
    app.include_router(registry.router)
    app.include_router(graph.router)
    app.include_router(soak.router)
    app.include_router(essays.router)
    app.include_router(omega.router)
    app.include_router(progress.router)
    app.include_router(atoms.router)
    app.include_router(ecosystem.router)
    app.include_router(pulse.router)
    app.include_router(ontologia.router)
    app.include_router(content.router)
    app.include_router(testament.router)
    app.include_router(network.router)
    app.include_router(trivium.router)
    app.include_router(irf.router)
    app.include_router(api_v1.router)

    @app.get("/")
    async def index():
        """Root redirect to health dashboard."""
        return RedirectResponse(url="/health/")

    return app


app = create_app()


def main():
    """CLI entry point."""
    import uvicorn
    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=8000, reload=True)
