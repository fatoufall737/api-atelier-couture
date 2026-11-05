from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import Conflit, NonTrouve
from app.models import Client, Commande
from app.schemas.client import ClientCreate, ClientUpdate
from app.telephone import normaliser_telephone


def _verifier_telephone_libre(db: Session, telephone: str, sauf_id: int | None = None) -> None:
    requete = select(Client.id).where(Client.telephone == telephone)
    if sauf_id is not None:
        requete = requete.where(Client.id != sauf_id)  # garder son propre numéro n'est pas un doublon
    if db.scalar(requete):
        raise Conflit(f"Un client avec le téléphone {telephone} existe déjà")


def obtenir(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise NonTrouve(f"Client {client_id} introuvable")
    return client


def creer(db: Session, data: ClientCreate) -> Client:
    _verifier_telephone_libre(db, data.telephone)
    client = Client(**data.model_dump())
    db.add(client)
    db.flush()
    return client


def lister(
    db: Session, q: str | None, genre: str | None, limit: int, offset: int
) -> tuple[list[Client], int]:
    requete = select(Client)
    if q:
        motif = f"%{q.strip()}%"
        conditions = [Client.nom.ilike(motif), Client.prenom.ilike(motif)]
        try:
            # on cherche aussi le numéro sous sa forme normalisée : "77 12" trouve "771234567"
            conditions.append(Client.telephone.ilike(f"%{normaliser_telephone(q)}%"))
        except ValueError:
            conditions.append(Client.telephone.ilike(motif))
        requete = requete.where(or_(*conditions))
    if genre:
        requete = requete.where(Client.genre == genre)
    total = db.scalar(select(func.count()).select_from(requete.subquery())) or 0
    items = db.scalars(
        requete.order_by(Client.nom, Client.prenom).limit(limit).offset(offset)
    ).all()
    return list(items), total


def modifier(db: Session, client: Client, data: ClientUpdate) -> Client:
    champs = data.model_dump(exclude_unset=True)
    if "telephone" in champs:
        _verifier_telephone_libre(db, champs["telephone"], sauf_id=client.id)
    for nom, valeur in champs.items():
        setattr(client, nom, valeur)
    db.flush()
    return client


def a_des_commandes(db: Session, client: Client) -> bool:
    return db.scalar(select(Commande.id).where(Commande.client_id == client.id).limit(1)) is not None


def supprimer(db: Session, client: Client) -> None:
    # RG4 : un client qui a des commandes ne peut pas être supprimé
    if a_des_commandes(db, client):
        raise Conflit("Ce client a des commandes : suppression impossible")
    db.delete(client)  # supprime aussi ses mesures (cascade du modèle)
    db.flush()