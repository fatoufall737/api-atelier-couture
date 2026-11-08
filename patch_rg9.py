p = "app/services/commande_service.py"
s = open(p, encoding="utf-8-sig").read()

ancien = "        mesure_id=donnees.mesure_id,"
nouveau = "        mesure_id=mesure_defaut,"
assert s.count(ancien) == 1, "ligne mesure_id introuvable"
s = s.replace(ancien, nouveau)

marque = "    commande = Commande("
assert s.count(marque) == 1, "bloc Commande introuvable"
ajout = (
    "    mesure_defaut = donnees.mesure_id\n"
    "    if mesure_defaut is None:\n"
    "        derniere = db.scalars(\n"
    "            select(Mesure)\n"
    "            .where(Mesure.client_id == donnees.client_id)\n"
    "            .order_by(Mesure.date_prise.desc(), Mesure.id.desc())\n"
    "        ).first()\n"
    "        mesure_defaut = derniere.id if derniere else None\n\n"
)
s = s.replace(marque, ajout + marque)
open(p, "w", encoding="utf-8").write(s)
print("OK : RG9 ajoute")
