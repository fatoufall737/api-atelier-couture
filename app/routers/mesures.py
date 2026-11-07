from fastapi import APIRouter, Response, status

from app.deps import DbSession, Tailleur, UtilisateurConnecte
from app.schemas.mesure import MesureCreate, MesureRead, MesureUpdate
from app.services import mesure_service
from app.exceptions import NonTrouve, Conflit, DonneesInvalides

router = APIRouter(tags=["Mensurations"])


@router.post(
    "/clients/{client_id}/mesures",
    response_model=MesureRead,
    status_code=status.HTTP_201_CREATED,
)
def creer(
    client_id: int,
    data: MesureCreate,
    db: DbSession,
    utilisateur: Tailleur,
):
    return mesure_service.creer_mesure(
        db, client_id, utilisateur.id, data
    )


@router.get(
    "/clients/{client_id}/mesures",
    response_model=list[MesureRead],
)
def historique(
    client_id: int,
    db: DbSession,
    _: UtilisateurConnecte,
):
    return mesure_service.obtenir_historique_mesures(db, client_id)


@router.get(
    "/clients/{client_id}/mesures/derniere",
    response_model=MesureRead,
)
def derniere(
    client_id: int,
    db: DbSession,
    _: UtilisateurConnecte,
):
    mesure = mesure_service.obtenir_derniere_mesure(db, client_id)

    if mesure is None:
        raise NonTrouve("Aucune mensuration trouvée pour ce client.")

    return mesure


@router.get("/mesures/{mesure_id}", response_model=MesureRead)
def detail(
    mesure_id: int,
    db: DbSession,
    _: UtilisateurConnecte,
):
    mesure = mesure_service.obtenir_mesure_par_id(db, mesure_id)

    if mesure is None:
        raise NonTrouve("Mensuration introuvable.")

    return mesure


@router.patch("/mesures/{mesure_id}", response_model=MesureRead)
def modifier(
    mesure_id: int,
    data: MesureUpdate,
    db: DbSession,
    _: Tailleur,
):
    mesure = mesure_service.obtenir_mesure_par_id(db, mesure_id)

    if mesure is None:
        raise NonTrouve("Mensuration introuvable.")

    try:
        return mesure_service.modifier_mesure(db, mesure, data)
    except ValueError as erreur:
        raise DonneesInvalides(str(erreur))


@router.delete(
    "/mesures/{mesure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def supprimer(
    mesure_id: int,
    db: DbSession,
    _: Tailleur,
):
    mesure = mesure_service.obtenir_mesure_par_id(db, mesure_id)

    if mesure is None:
        raise NonTrouve("Mensuration introuvable.")

    try:
        mesure_service.supprimer_mesure(db, mesure)
    except ValueError as erreur:
        raise Conflit(str(erreur))

    return Response(status_code=status.HTTP_204_NO_CONTENT)