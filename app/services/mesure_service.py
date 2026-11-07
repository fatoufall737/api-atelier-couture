from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mesure import Mesure, CHAMPS_MESURES
from app.models.commande import Commande
from app.schemas.mesure import MesureCreate, MesureUpdate


def creer_mesure(
    db: Session,
    client_id: int,
    prise_par_id: int,
    donnees: MesureCreate,
) -> Mesure:

    nouvelle_mesure = Mesure(
        client_id=client_id,
        prise_par_id=prise_par_id,
        **donnees.model_dump(exclude_unset=True),
    )

    db.add(nouvelle_mesure)
    db.commit()
    db.refresh(nouvelle_mesure)

    return nouvelle_mesure


def obtenir_historique_mesures(
    db: Session,
    client_id: int,
) -> list[Mesure]:

    requete = (
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
    )

    return db.scalars(requete).all()


def obtenir_derniere_mesure(
    db: Session,
    client_id: int,
) -> Mesure | None:

    requete = (
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
        .limit(1)
    )

    return db.scalars(requete).first()


def obtenir_mesure_par_id(
    db: Session,
    mesure_id: int,
) -> Mesure | None:

    return db.get(Mesure, mesure_id)


def modifier_mesure(
    db: Session,
    mesure: Mesure,
    donnees: MesureUpdate,
) -> Mesure:

    modifications = donnees.model_dump(exclude_unset=True)

    valeurs_finales = {
        champ: modifications.get(champ, getattr(mesure, champ))
        for champ in CHAMPS_MESURES
    }

    if not any(
        valeur is not None
        for valeur in valeurs_finales.values()
    ):
        raise ValueError(
            "Une fiche doit conserver au moins une mensuration."
        )

    for champ, valeur in modifications.items():
        setattr(mesure, champ, valeur)

    db.commit()
    db.refresh(mesure)

    return mesure


def supprimer_mesure(
    db: Session,
    mesure: Mesure,
) -> None:

    commande_existante = db.scalar(
        select(Commande.id).where(Commande.mesure_id == mesure.id)
    )

    if commande_existante is not None:
        raise ValueError(
            "Impossible de supprimer cette mensuration : "
            "elle est utilisée par une commande."
        )

    db.delete(mesure)
    db.commit()