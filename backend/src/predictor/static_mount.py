import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


def mount_static(app):
    """Mount frontend static files for production (Docker) serving."""
    static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static')
    if os.path.isdir(static_dir):
        @app.get('/{path:path}')
        async def serve_spa(path: str):
            file_path = os.path.join(static_dir, path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(static_dir, 'index.html'))
