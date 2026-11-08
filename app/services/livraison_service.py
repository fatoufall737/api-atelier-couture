from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import Conflit, DonneesInvalides, NonTrouve
from app.models.client import Client
from app.models.commande import Commande, HistoriqueStatut, Livraison
from app.services.commande_edition_service import STATUTS_FINAUX, get_commande


def planifier(db: Session, commande_id: int, d: dict) -> Livraison:
    commande = get_commande(db, commande_id)
    if commande.statut in STATUTS_FINAUX:
        raise Conflit("Commande " + commande.statut + " : la livraison n'est plus modifiable")
    if d["mode"] == "domicile" and not (d.get("adresse") or "").strip():
        raise DonneesInvalides("Une livraison a domicile exige une adresse")
    if d["date_prevue"] < commande.date_commande:
        raise DonneesInvalides("La date prevue ne peut pas preceder la date de commande")

    livraison = commande.livraison
    if livraison is None:
        livraison = Livraison(commande_id=commande.id, statut="planifiee")
        db.add(livraison)
    livraison.mode = d["mode"]
    livraison.adresse = d.get("adresse")
    livraison.livreur = d.get("livreur")
    livraison.date_prevue = d["date_prevue"]
    livraison.notes = d.get("notes")
    commande.date_livraison_prevue = d["date_prevue"]
    db.flush()
    return livraison


def confirmer(db: Session, commande_id: int, d: dict, utilisateur) -> Livraison:
    commande = get_commande(db, commande_id)
    if commande.statut != "terminee":
        raise Conflit("La livraison exige une commande terminee (statut actuel : " + commande.statut + ")")
    solde = commande.montant_total - commande.montant_paye
    autorise = bool(d.get("autoriser_solde_impaye"))
    if solde > 0 and not autorise:
        raise Conflit("Commande non soldee : " + str(solde) + " FCFA impayes. "
                      "Encaissez le solde ou envoyez autoriser_solde_impaye = true")

    date_effective = d.get("date_effective") or date.today()
    livraison = commande.livraison
    if livraison is None:
        livraison = Livraison(commande_id=commande.id, mode="retrait_atelier", date_prevue=date_effective)
        db.add(livraison)
    livraison.date_effective = date_effective
    livraison.statut = "livree"

    commentaire = "Livraison confirmee"
    if solde > 0:
        commentaire += " avec solde impaye de " + str(solde) + " FCFA (autorise)"
    commande.historique.append(HistoriqueStatut(
        ancien_statut=commande.statut, nouveau_statut="livree",
        commentaire=commentaire, utilisateur_id=utilisateur.id,
    ))
    commande.statut = "livree"
    commande.date_livraison_reelle = date_effective
    db.flush()
    return livraison


def lire(db: Session, commande_id: int) -> Livraison:
    commande = get_commande(db, commande_id)
    if commande.livraison is None:
        raise NonTrouve("Aucune livraison planifiee pour cette commande")
    return commande.livraison


def sortie(l: Livraison) -> dict:
    return {
        "id": l.id, "commande_id": l.commande_id, "mode": l.mode, "adresse": l.adresse,
        "livreur": l.livreur, "date_prevue": l.date_prevue, "date_effective": l.date_effective,
        "statut": l.statut, "notes": l.notes,
    }


def lister(db: Session, statut, date_min, date_max, limit: int, offset: int):
    conds = []
    if statut:
        conds.append(Livraison.statut == statut)
    if date_min:
        conds.append(Livraison.date_prevue >= date_min)
    if date_max:
        conds.append(Livraison.date_prevue <= date_max)
    total = db.scalar(select(func.count(Livraison.id)).where(*conds)) or 0
    lignes = db.execute(
        select(Livraison, Commande, Client)
        .join(Commande, Livraison.commande_id == Commande.id)
        .join(Client, Commande.client_id == Client.id)
        .where(*conds)
        .order_by(Livraison.date_prevue, Livraison.id)
        .limit(limit).offset(offset)
    ).all()
    items = []
    for liv, cmd, cli in lignes:
        item = sortie(liv)
        item["numero_commande"] = cmd.numero
        item["client_nom"] = cli.prenom + " " + cli.nom
        item["client_telephone"] = cli.telephone
        item["solde_commande"] = cmd.montant_total - cmd.montant_paye
        items.append(item)
    return items, total
