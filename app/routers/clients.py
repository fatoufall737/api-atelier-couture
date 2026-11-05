from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.deps import Admin, DbSession, UtilisateurConnecte
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate, Genre
from app.schemas.common import Page
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def creer(data: ClientCreate, db: DbSession, _: UtilisateurConnecte):
    client = client_service.creer(db, data)
    db.commit()
    return client


@router.get("", response_model=Page[ClientRead])
def lister(
    db: DbSession,
    _: UtilisateurConnecte,
    q: Annotated[str | None, Query(min_length=2)] = None,
    genre: Genre | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = client_service.lister(db, q, genre, limit, offset)
    return Page(
        items=[ClientRead.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{client_id}", response_model=ClientRead)
def detail(client_id: int, db: DbSession, _: UtilisateurConnecte):
    return client_service.obtenir(db, client_id)


@router.patch("/{client_id}", response_model=ClientRead)
def modifier(client_id: int, data: ClientUpdate, db: DbSession, _: UtilisateurConnecte):
    client = client_service.obtenir(db, client_id)
    client_service.modifier(db, client, data)
    db.commit()
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer(client_id: int, db: DbSession, _: Admin):
    client = client_service.obtenir(db, client_id)
    client_service.supprimer(db, client)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)