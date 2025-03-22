from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


# Static Files
def bind_static(api: FastAPI, dist_dir: str = "dist"):
    api.mount("/assets", StaticFiles(directory=f"{dist_dir}/app/assets"), name="static")

    @api.get("/{all_paths:path}")
    async def serve_app(all_paths: str):
        return FileResponse(f"{dist_dir}/app/index.html")
