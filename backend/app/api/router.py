from fastapi import APIRouter
from backend.app.api.endpoints import sonar, contacts, gis, reports, ws

api_router = APIRouter()

api_router.include_router(sonar.router, prefix="/sonar", tags=["sonar"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(gis.router, prefix="/gis", tags=["gis"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
