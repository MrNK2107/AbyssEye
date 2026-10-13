from fastapi import APIRouter
from backend.app.api.endpoints import sonar, contacts, gis, reports, ws

api_router = APIRouter()

api_router.include_router(sonar.router, prefix="/sonar", tags=["sonar"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(gis.router, prefix="/gis", tags=["gis"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])

# Top-level route aliases for frontend client compatibility
api_router.add_api_route("/model", sonar.get_model_performance, methods=["GET"], tags=["model"])
api_router.add_api_route("/samples", sonar.get_sample_library, methods=["GET"], tags=["samples"])
api_router.add_api_route("/analyze", sonar.analyze_sonar_image, methods=["POST"], tags=["analyze"])
