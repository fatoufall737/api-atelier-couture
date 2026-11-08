import getpass
import random
import re
from datetime import date, timedelta

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
http = httpx.Client(timeout=20)
resultats = []


def verifier(etape, reponse, attendu, **details):
    ok = reponse.status_code == attendu
    resultats.append(ok)
    marque = "OK    " if ok else "ECHEC "
    texte = f"{marque}{etape} : code {reponse.status_code} (attendu {attendu})"
    if not ok:
        texte += f" -> {reponse.text[:200]}"
    print(texte)
    for nom, valeur in details.items():
        print(f"        {nom} = {valeur}")
    return reponse


def controle(etape, condition, valeur=""):
    resultats.append(bool(condition))
    print(f"{'OK    ' if condition else 'ECHEC '}{etape} {valeur}")


def connexion(email, mot_de_passe):
    r = http.post(f"{BASE}/auth/login", data={"username": email, "password": mot_de_passe})
    if r.status_code != 200:
        raise SystemExit(f"Connexion impossible pour {email} : {r.status_code} {r.text}")
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


accueil = connexion("accueil@atelier.sn", "Accueil2026!")
tailleur = connexion("tailleur@atelier.sn", "Tailleur2026!")
admin = connexion("admin@atelier.sn", getpass.getpass("Mot de passe admin (saisie masquee) : "))

print("\n=== Etape 1 : cliente et doublon ===")
chiffres = "".join(random.choice("0123456789") for _ in range(7))
r = verifier("Creation de la cliente", http.post(
    f"{BASE}/clients", headers=accueil,
    json={"nom": "Diop", "prenom": "Fatou", "telephone": f"77 {chiffres[:3]} {chiffres[3:5]} {chiffres[5:]}"}), 201)
client_id = r.json()["id"]
controle("Telephone normalise (sans espaces)", r.json()["telephone"] == f"77{chiffres}", r.json()["telephone"])
verifier("Doublon refuse", http.post(
    f"{BASE}/clients", headers=accueil,
    json={"nom": "Ndiaye", "prenom": "Awa", "telephone": f"77{chiffres}"}), 409)

print("\n=== Etape 2 : mesures ===")
verifier("Accueil ne peut pas prendre de mesures", http.post(
    f"{BASE}/clients/{client_id}/mesures", headers=accueil, json={"tour_taille": 80}), 403)
r = verifier("Tailleur prend les mesures", http.post(
    f"{BASE}/clients/{client_id}/mesures", headers=tailleur,
    json={"tour_taille": 80, "tour_poitrine": 95, "longueur_manche": 60}), 201)
mesure_id = r.json()["id"]

print("\n=== Etape 3 : commande ===")
r = verifier("Creation de la commande", http.post(
    f"{BASE}/commandes", headers=accueil,
    json={"client_id": client_id, "remise": 5000, "lignes": [
        {"type_vetement_id": 1, "description": "Boubou brode", "quantite": 2, "prix_unitaire": 35000},
        {"type_vetement_id": 6, "description": "Pantalon negocie", "quantite": 1, "prix_unitaire": 10000}]}), 201)
cmd = r.json()
cid = cmd["id"]
controle("Numero CMD-AAAA-NNNNN", re.fullmatch(r"CMD-\d{4}-\d{5}", cmd["numero"]), cmd["numero"])
controle("Statut initial en_attente", cmd["statut"] == "en_attente", cmd["statut"])
controle("Total = 75000", cmd["montant_total"] == 75000, cmd["montant_total"])
prevue = (date.today() + timedelta(days=10)).isoformat()
controle("Date prevue = +10 jours (RG8)", str(cmd["date_livraison_prevue"])[:10] == prevue, cmd["date_livraison_prevue"])
controle("Mesures rattachees automatiquement (RG9)", cmd["mesure_id"] == mesure_id, cmd["mesure_id"])

print("\n=== Etape 4 : transition interdite ===")
r = verifier("en_attente -> terminee refuse", http.post(
    f"{BASE}/commandes/{cid}/statut", headers=accueil, json={"statut": "terminee"}), 409)
print("        message =", r.json().get("detail"))

print("\n=== Etape 5 : production par le tailleur ===")
for statut in ["en_coupe", "en_couture", "essayage", "retouches", "essayage", "terminee"]:
    verifier(f"Statut -> {statut}", http.post(
        f"{BASE}/commandes/{cid}/statut", headers=tailleur, json={"statut": statut}), 200)
r = verifier("Historique", http.get(f"{BASE}/commandes/{cid}/historique", headers=accueil), 200)
controle("Historique = 7 lignes (creation + 6 changements)", len(r.json()) == 7, len(r.json()))

print("\n=== Etape 6 : acompte ===")
verifier("Acompte Wave 30000", http.post(
    f"{BASE}/commandes/{cid}/paiements", headers=accueil, json={"montant": 30000, "mode": "wave"}), 201)
verifier("Paiement superieur au solde refuse", http.post(
    f"{BASE}/commandes/{cid}/paiements", headers=accueil, json={"montant": 100000, "mode": "especes"}), 409)

print("\n=== Etape 7 : livraison avec solde impaye ===")
verifier("Confirmation refusee (solde non paye)", http.post(
    f"{BASE}/commandes/{cid}/livraison/confirmer", headers=accueil), 409)

print("\n=== Etape 8 : solde puis livraison ===")
verifier("Paiement du solde 45000", http.post(
    f"{BASE}/commandes/{cid}/paiements", headers=accueil, json={"montant": 45000, "mode": "especes"}), 201)
verifier("Confirmation de livraison", http.post(
    f"{BASE}/commandes/{cid}/livraison/confirmer", headers=accueil), 200)
r = http.get(f"{BASE}/commandes/{cid}", headers=accueil)
controle("Commande livree", r.json().get("statut") == "livree", r.json().get("statut"))
controle("Solde a 0", r.json().get("solde", 0) == 0, r.json().get("solde"))

print("\n=== Etape 9 : statistiques ===")
r = verifier("Tableau de bord (admin)", http.get(f"{BASE}/statistiques/tableau-de-bord", headers=admin), 200)
print("        chiffre_affaires_mois =", r.json().get("chiffre_affaires_mois"))
verifier("Accueil refuse sur les statistiques", http.get(f"{BASE}/statistiques/tableau-de-bord", headers=accueil), 403)

print("\n=== Etape 10 : impayes et retards ===")
verifier("Impayes (admin)", http.get(f"{BASE}/statistiques/impayes", headers=admin), 200)
verifier("Commandes en retard", http.get(f"{BASE}/commandes", headers=accueil, params={"en_retard": "true"}), 200)

print(f"\nBILAN : {sum(resultats)} controles reussis sur {len(resultats)}")