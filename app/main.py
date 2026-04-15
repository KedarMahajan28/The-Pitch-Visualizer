
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv


load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routes.export import router as export_router
from app.routes.storyboard import router as storyboard_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Pitch Visualizer API starting up.")
    yield
    logging.getLogger(__name__).info("Pitch Visualizer API shutting down.")


app = FastAPI(
    title="Pitch Visualizer API",
    description=(
        "Transforms narrative paragraphs into AI-generated storyboards. "
        "Uses Gemini 1.5 Flash (primary) with Groq/Llama-3 fallback for prompt generation, "
        "and Hugging Face Inference API for image synthesis."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(storyboard_router, prefix="/api", tags=["Storyboard"])
app.include_router(export_router,     prefix="/api", tags=["Export"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "docs": "/docs"}

# Mount the basic frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    logging.getLogger(__name__).warning("Frontend directory not found. UI will not be served.")
