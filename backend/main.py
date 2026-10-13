from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="ABYSSEYE: AI-Powered Automated Underwater Marine Debris and Anomaly Detection System (SIH 2026 Problem 26057)"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "ABYSSEYE-BACKEND",
        "version": "3.0.0",
        "pipeline_state": "READY"
    }

# Mount Gradio demo interface
try:
    import gradio as gr
    from backend.app.services.gradio_app import create_gradio_interface
    gradio_demo = create_gradio_interface()
    app = gr.mount_gradio_app(app, gradio_demo, path="/gradio")
except Exception as e:
    print(f"Gradio mounting note: {e}")

# Mount static frontend build if present
import os
from fastapi.staticfiles import StaticFiles

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "out"))
if not os.path.exists(frontend_dir):
    frontend_dir = os.path.abspath("frontend/out")
if not os.path.exists(frontend_dir) and os.path.exists("index.html"):
    frontend_dir = os.path.abspath(".")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
