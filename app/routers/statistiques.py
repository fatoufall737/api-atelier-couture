from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.deps import Admin, DbSession
from app.services import statistique_service

router = APIRouter(prefix="/statistiques", tags=["Statistiques"])


def _periode(date_debut: date | None, date_fin: date | None):
    # Par défaut : du 1er du mois à aujourd'hui
    aujourdhui = date.today()
    return date_debut or aujourdhui.replace(day=1), date_fin or aujourdhui


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
    debut, fin = _periode(date_debut, date_fin)
    return statistique_service.chiffre_affaires_par_periode(
        db, granularite, debut, fin
    )


@router.get("/types-vetement")
def types_vetement(
    db: DbSession,
    _: Admin,
    date_debut: date | None = None,
    date_fin: date | None = None,
):
    debut, fin = _periode(date_debut, date_fin)
    return statistique_service.ventes_par_type_vetement(db, debut, fin)


@router.get("/top-clients")
def top_clients(
    db: DbSession,
    _: Admin,
    date_debut: date | None = None,
    date_fin: date | None = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 10,
):
    debut, fin = _periode(date_debut, date_fin)
    return statistique_service.meilleurs_clients(db, debut, fin, limite)


@router.get("/impayes")
def impayes(
    db: DbSession,
    _: Admin,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = statistique_service.commandes_impayees(db, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}