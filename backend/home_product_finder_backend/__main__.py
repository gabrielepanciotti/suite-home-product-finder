"""Entry point: `python -m home_product_finder_backend` starts uvicorn.

Port is read from env `PORT` (default 8000); in dev/prod it is set to 10008
(menu.ps1 exports PORT=10008, the Dockerfile sets ENV PORT=10008).
Reload is enabled via env `UVICORN_RELOAD=1` (used in dev by menu.ps1).
"""
import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "home_product_finder_backend.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("UVICORN_RELOAD") == "1",
    )


if __name__ == "__main__":
    main()
