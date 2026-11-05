from fastapi import APIRouter, status

from app.deps import Admin, DbSession
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurRead, UtilisateurUpdate
from app.services import utilisateur_service

router = APIRouter(prefix="/utilisateurs", tags=["Utilisateurs"])


@router.post("", response_model=UtilisateurRead, status_code=status.HTTP_201_CREATED)
def creer(data: UtilisateurCreate, db: DbSession, _: Admin):
    utilisateur = utilisateur_service.creer(db, data)
    db.commit()
    return utilisateur


@router.get("", response_model=list[UtilisateurRead])
def lister(db: DbSession, _: Admin):
    return utilisateur_service.lister(db)


@router.get("/{utilisateur_id}", response_model=UtilisateurRead)
def detail(utilisateur_id: int, db: DbSession, _: Admin):
    return utilisateur_service.obtenir(db, utilisateur_id)


@router.patch("/{utilisateur_id}", response_model=UtilisateurRead)
def modifier(utilisateur_id: int, data: UtilisateurUpdate, db: DbSession, courant: Admin):
    cible = utilisateur_service.obtenir(db, utilisateur_id)
    utilisateur_service.modifier(db, cible, data, courant)
    db.commit()
    return cible