from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import DbSession, UtilisateurConnecte
from app.services import client_commandes_service

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/{client_id}/commandes")
def lister_commandes_du_client(
    client_id: int,
    db: DbSession,
    _: UtilisateurConnecte,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = client_commandes_service.commandes_du_client(
        db, client_id, limit, offset
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{client_id}/resume")
def resume_du_client(client_id: int, db: DbSession, _: UtilisateurConnecte):
    return client_commandes_service.resume_client(db, client_id)