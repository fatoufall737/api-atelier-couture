from fastapi import APIRouter

from app.deps import Admin, DbSession
from app.services import statistique_service

router = APIRouter(prefix="/statistiques", tags=["Statistiques"])


@router.get("/tableau-de-bord")
def tableau_de_bord(db: DbSession, _: Admin):
    return statistique_service.tableau_de_bord(db)