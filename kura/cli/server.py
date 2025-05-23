from fastapi import FastAPI, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

api = FastAPI()

# Configure CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve static files from web/dist
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")


# Serve static files from web/dist at the root
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")

# Mount static files at root
api.mount("/", staticfiles.StaticFiles(directory=str(web_dir), html=True))
