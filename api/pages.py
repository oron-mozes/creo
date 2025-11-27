from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse


def build_pages_router(project_root: Path) -> APIRouter:
    router = APIRouter()

    build_dir = project_root / "build"
    static_app = "static/app.html"
    build_index = build_dir / "index.html"

    @router.get("/")
    def read_root():
        """Serve the unified SPA (React build in production, fallback to static/app.html in dev)."""
        if build_index.exists():
            return FileResponse(build_index)
        return FileResponse(static_app)

    @router.get("/index.html")
    def index_page():
        """Redirect index.html to unified SPA."""
        if build_index.exists():
            return FileResponse(build_index)
        return FileResponse(static_app)

    def _spa_response():
        if build_index.exists():
            return FileResponse(build_index)
        return FileResponse(static_app)

    @router.get("/creators")
    def creators_page():
        """Serve SPA for creators viewer."""
        return _spa_response()

    @router.get("/login")
    @router.get("/login.html")
    def login_page():
        """Serve SPA for login route (React handles modals)."""
        return _spa_response()

    @router.get("/chat/{session_id}")
    def chat_page(session_id: str):
        """Serve the unified SPA for chat sessions."""
        return _spa_response()

    @router.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "agent": "orchestrator"}

    return router
