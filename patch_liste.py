p = "app/routers/commandes.py"
s = open(p, encoding="utf-8-sig").read()
debut = s.index('@router.get("/commandes", response_model=list[CommandeRead])')
suite = s.find("\n@router.", debut + 10)
fin_classe = s.find("\nclass ", debut + 10)
candidats = [x for x in (suite, fin_classe) if x != -1]
fin = (min(candidats) + 1) if candidats else len(s)
nouveau = '''@router.get("/commandes")
def lister_commandes(
    db: DbSession,
    _: UtilisateurConnecte,
    statut: str | None = None,
    client_id: int | None = None,
    en_retard: bool | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    numero: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from sqlalchemy import and_, func
    from app.models.client import Client

    retard = and_(
        Commande.date_livraison_prevue < date.today(),
        Commande.statut.notin_(["livree", "annulee"]),
    )
    conds = []
    if statut:
        conds.append(Commande.statut == statut)
    if client_id:
        conds.append(Commande.client_id == client_id)
    if en_retard is True:
        conds.append(retard)
    if en_retard is False:
        conds.append(~retard)
    if date_min:
        conds.append(Commande.date_commande >= date_min)
    if date_max:
        conds.append(Commande.date_commande <= date_max)
    if numero:
        conds.append(Commande.numero.ilike("%" + numero + "%"))

    total = db.scalar(select(func.count(Commande.id)).where(*conds)) or 0
    rows = db.execute(
        select(Commande, Client)
        .join(Client, Commande.client_id == Client.id)
        .where(*conds)
        .order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    items = []
    for c, cli in rows:
        items.append({
            "id": c.id,
            "numero": c.numero,
            "client_id": c.client_id,
            "client_nom": cli.prenom + " " + cli.nom,
            "statut": c.statut,
            "date_commande": c.date_commande,
            "date_livraison_prevue": c.date_livraison_prevue,
            "montant_total": c.montant_total,
            "montant_paye": c.montant_paye,
            "solde": c.montant_total - c.montant_paye,
            "en_retard": c.date_livraison_prevue < date.today()
            and c.statut not in ("livree", "annulee"),
        })
    return {"items": items, "total": total, "limit": limit, "offset": offset}


'''
s = s[:debut] + nouveau + s[fin:]
if "Query" not in s.split("router = APIRouter")[0]:
    s = "from fastapi import Query\n" + s
open(p, "w", encoding="utf-8").write(s)
print("OK : liste des commandes mise a jour")
