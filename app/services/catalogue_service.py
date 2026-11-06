from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import Conflit, NonTrouve
from app.models import TypeVetement
from app.schemas.catalogue import TypeVetementCreate, TypeVetementUpdate


def _verifier_nom_libre(db: Session, nom: str, sauf_id: int | None = None) -> None:
    requete = select(TypeVetement.id).where(TypeVetement.nom == nom)
    if sauf_id is not None:
        requete = requete.where(TypeVetement.id != sauf_id)
    if db.scalar(requete):
        raise Conflit(f"Une prestation nommée « {nom} » existe déjà")


def creer(db: Session, data: TypeVetementCreate) -> TypeVetement:
    _verifier_nom_libre(db, data.nom)
    prestation = TypeVetement(**data.model_dump())
    db.add(prestation)
    db.flush()
    return prestation


def lister(db: Session, actifs_seulement: bool) -> list[TypeVetement]:
    requete = select(TypeVetement).order_by(TypeVetement.nom)
    if actifs_seulement:
        requete = requete.where(TypeVetement.actif.is_(True))
    return list(db.scalars(requete))


def obtenir(db: Session, prestation_id: int) -> TypeVetement:
    prestation = db.get(TypeVetement, prestation_id)
    if prestation is None:
        raise NonTrouve(f"Prestation {prestation_id} introuvable")
    return prestation


def modifier(db: Session, prestation: TypeVetement, data: TypeVetementUpdate) -> TypeVetement:
    champs = data.model_dump(exclude_unset=True)
    # ces champs sont obligatoires en base : un null explicite est ignoré
    for obligatoire in ("nom", "prix_base", "delai_jours", "actif"):
        if obligatoire in champs and champs[obligatoire] is None:
            champs.pop(obligatoire)
    if "nom" in champs:
        _verifier_nom_libre(db, champs["nom"], sauf_id=prestation.id)
    for nom, valeur in champs.items():
        setattr(prestation, nom, valeur)
    db.flush()
    return prestation