import pytest

P = "/api/v1"


@pytest.fixture()
def cmd(client, headers):
    c = client.post(f"{P}/clients", headers=headers["accueil"],
                    json={"nom": "Diop", "prenom": "Fatou", "telephone": "771234567"}).json()
    bou = client.post(f"{P}/catalogue", headers=headers["admin"],
                      json={"nom": "Boubou", "prix_base": 35000, "delai_jours": 10}).json()
    r = client.post(f"{P}/commandes", headers=headers["accueil"], json={
        "client_id": c["id"], "lignes": [{"type_vetement_id": bou["id"], "quantite": 2}],
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_route25_liste_paginee_avec_champs(client, headers, cmd):
    r = client.get(f"{P}/commandes", headers=headers["tailleur"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] == 1 and d["limit"] == 20 and d["offset"] == 0
    item = d["items"][0]
    assert item["client_nom"] == "Fatou Diop"
    assert item["solde"] == 70000
    assert item["en_retard"] is False


def test_route25_filtre_statut(client, headers, cmd):
    r = client.get(f"{P}/commandes?statut=livree", headers=headers["admin"])
    assert r.json()["total"] == 0


def test_route26_detail_complet(client, headers, cmd):
    r = client.get(f"{P}/commandes/{cmd['id']}", headers=headers["tailleur"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["solde"] == 70000
    assert d["lignes"][0]["prestation"] == "Boubou"
    assert d["lignes"][0]["sous_total"] == 70000
    assert d["paiements"] == [] and d["livraison"] is None


def test_route26_commande_inconnue_404(client, headers):
    assert client.get(f"{P}/commandes/99999", headers=headers["admin"]).status_code == 404
