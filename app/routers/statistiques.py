from datetime import date
from typing import Literal

from fastapi import APIRouter

from app.deps import Admin, DbSession
from app.services import statistique_service

router = APIRouter(prefix="/statistiques", tags=["Statistiques"])


@router.get("/tableau-de-bord")
def tableau_de_bord(db: DbSession, _: Admin):
    return statistique_service.tableau_de_bord(db)


@router.get("/chiffre-affaires")
def chiffre_affaires(
    db: DbSession,
    _: Admin,
    granularite: Literal["jour", "mois"] = "jour",
    date_debut: date | None = None,
    date_fin: date | None = None,
):
    # Par défaut : du 1er du mois à aujourd'hui
    aujourdhui = date.today()
    debut = date_debut or aujourdhui.replace(day=1)
    fin = date_fin or aujourdhui
    return statistique_service.chiffre_affaires_par_periode(
        db, granularite, debut, fin
    )