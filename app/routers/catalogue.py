from fastapi import APIRouter, status

from app.deps import Admin, DbSession, UtilisateurConnecte
from app.schemas.catalogue import TypeVetementCreate, TypeVetementRead, TypeVetementUpdate
from app.services import catalogue_service

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])


@router.post("", response_model=TypeVetementRead, status_code=status.HTTP_201_CREATED)
def creer(data: TypeVetementCreate, db: DbSession, _: Admin):
    prestation = catalogue_service.creer(db, data)
    db.commit()
    return prestation


@router.get("", response_model=list[TypeVetementRead])
def lister(db: DbSession, _: UtilisateurConnecte, actifs_seulement: bool = True):
    return catalogue_service.lister(db, actifs_seulement)


@router.get("/{prestation_id}", response_model=TypeVetementRead)
def detail(prestation_id: int, db: DbSession, _: UtilisateurConnecte):
    return catalogue_service.obtenir(db, prestation_id)


@router.patch("/{prestation_id}", response_model=TypeVetementRead)
def modifier(prestation_id: int, data: TypeVetementUpdate, db: DbSession, _: Admin):
    prestation = catalogue_service.obtenir(db, prestation_id)
    catalogue_service.modifier(db, prestation, data)
    db.commit()
    return prestation