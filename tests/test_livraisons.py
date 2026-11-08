from datetime import date, timedelta

import pytest

P = "/api/v1"


def _jour(n):
    return (date.today() + timedelta(days=n)).isoformat()


@pytest.fixture()
def cmd(client, headers):
    """Commande de 75000 FCFA (2 boubous + 1 pantalon negocie, remise 5000)."""
    c = client.post(f"{P}/clients", headers=headers["accueil"],
                    json={"nom": "Diop", "prenom": "Fatou", "telephone": "771234567"}).json()
    bou = client.post(f"{P}/catalogue", headers=headers["admin"],
                      json={"nom": "Boubou", "prix_base": 35000, "delai_jours": 10}).json()
    pan = client.post(f"{P}/catalogue", headers=headers["admin"],
                      json={"nom": "Pantalon", "prix_base": 12000, "delai_jours": 4}).json()
    r = client.post(f"{P}/commandes", headers=headers["accueil"], json={
        "client_id": c["id"], "remise": 5000,
        "lignes": [{"type_vetement_id": bou["id"], "quantite": 2},
                   {"type_vetement_id": pan["id"], "quantite": 1, "prix_unitaire": 10000}],
    })
    assert r.status_code == 201, r.text
    return r.json()


def _terminer(client, headers, cid):
    for statut in ("en_coupe", "en_couture", "terminee"):
        r = client.post(f"{P}/commandes/{cid}/statut", headers=headers["tailleur"], json={"statut": statut})
        assert r.status_code == 200, r.text


def test_livraison_domicile_exige_adresse(client, headers, cmd):
    r = client.put(f"{P}/commandes/{cmd['id']}/livraison", headers=headers["accueil"],
                   json={"mode": "domicile", "date_prevue": _jour(5)})
    assert r.status_code == 422


def test_get_livraison_404_si_aucune(client, headers, cmd):
    r = client.get(f"{P}/commandes/{cmd['id']}/livraison", headers=headers["tailleur"])
    assert r.status_code == 404


def test_rg18_planifier_puis_replanifier_sans_doublon(client, headers, cmd):
    cid = cmd["id"]
    r1 = client.put(f"{P}/commandes/{cid}/livraison", headers=headers["accueil"],
                    json={"mode": "retrait_atelier", "date_prevue": _jour(5)})
    assert r1.status_code == 200, r1.text
    r2 = client.put(f"{P}/commandes/{cid}/livraison", headers=headers["accueil"],
                    json={"mode": "domicile", "adresse": "Rufisque", "date_prevue": _jour(7)})
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == r1.json()["id"]
    c = client.get(f"{P}/commandes/{cid}", headers=headers["admin"]).json()
    assert c["date_livraison_prevue"] == _jour(7)


def test_tailleur_ne_peut_pas_planifier(client, headers, cmd):
    r = client.put(f"{P}/commandes/{cmd['id']}/livraison", headers=headers["tailleur"],
                   json={"mode": "retrait_atelier", "date_prevue": _jour(5)})
    assert r.status_code == 403


def test_rg19_confirmer_exige_commande_terminee(client, headers, cmd):
    r = client.post(f"{P}/commandes/{cmd['id']}/livraison/confirmer", headers=headers["accueil"])
    assert r.status_code == 409


def test_rg19_confirmer_refuse_si_solde_impaye(client, headers, cmd):
    cid = cmd["id"]
    _terminer(client, headers, cid)
    r = client.post(f"{P}/commandes/{cid}/livraison/confirmer", headers=headers["accueil"])
    assert r.status_code == 409
    assert "75000" in r.json()["detail"]


def test_rg19_confirmer_avec_autorisation_solde_impaye(client, headers, cmd):
    cid = cmd["id"]
    _terminer(client, headers, cid)
    r = client.post(f"{P}/commandes/{cid}/livraison/confirmer", headers=headers["accueil"],
                    json={"autoriser_solde_impaye": True})
    assert r.status_code == 200, r.text
    c = client.get(f"{P}/commandes/{cid}", headers=headers["admin"]).json()
    assert c["statut"] == "livree"
    assert c["montant_paye"] == 0  # la dette reste visible


def test_rg20_confirmer_apres_solde_cree_livraison_et_passe_livree(client, headers, cmd):
    cid = cmd["id"]
    _terminer(client, headers, cid)
    p = client.post(f"{P}/commandes/{cid}/paiements", headers=headers["accueil"],
                    json={"montant": 75000, "mode": "wave"})
    assert p.status_code == 201, p.text
    r = client.post(f"{P}/commandes/{cid}/livraison/confirmer", headers=headers["accueil"])
    assert r.status_code == 200, r.text
    assert r.json()["statut"] == "livree" and r.json()["mode"] == "retrait_atelier"
    c = client.get(f"{P}/commandes/{cid}", headers=headers["admin"]).json()
    assert c["statut"] == "livree"
    assert c["date_livraison_reelle"] == date.today().isoformat()
    hist = client.get(f"{P}/commandes/{cid}/historique", headers=headers["admin"])
    assert hist.status_code == 200


def test_tailleur_ne_peut_pas_confirmer(client, headers, cmd):
    r = client.post(f"{P}/commandes/{cmd['id']}/livraison/confirmer", headers=headers["tailleur"])
    assert r.status_code == 403


def test_liste_livraisons_tournee(client, headers, cmd):
    client.put(f"{P}/commandes/{cmd['id']}/livraison", headers=headers["accueil"],
               json={"mode": "retrait_atelier", "date_prevue": _jour(5)})
    r = client.get(f"{P}/livraisons", headers=headers["tailleur"])
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["numero_commande"].startswith("CMD-")
    assert item["client_telephone"] == "771234567"
    assert item["solde_commande"] == 75000
