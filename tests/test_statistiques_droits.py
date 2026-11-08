import pytest

P = "/api/v1"

CHEMINS = [
    "/statistiques/tableau-de-bord",
    "/statistiques/chiffre-affaires",
    "/statistiques/types-vetement",
    "/statistiques/top-clients",
    "/statistiques/impayes",
]


@pytest.mark.parametrize("chemin", CHEMINS)
def test_statistiques_reservees_a_l_admin(client, headers, chemin):
    assert client.get(P + chemin, headers=headers["admin"]).status_code == 200
    assert client.get(P + chemin, headers=headers["accueil"]).status_code == 403
    assert client.get(P + chemin, headers=headers["tailleur"]).status_code == 403
    assert client.get(P + chemin).status_code == 401


def test_commande_annulee_exclue_des_impayes(client, headers):
    c = client.post(f"{P}/clients", headers=headers["accueil"],
                    json={"nom": "Diop", "prenom": "Fatou", "telephone": "771234567"}).json()
    bou = client.post(f"{P}/catalogue", headers=headers["admin"],
                      json={"nom": "Boubou", "prix_base": 35000, "delai_jours": 10}).json()
    r = client.post(f"{P}/commandes", headers=headers["accueil"], json={
        "client_id": c["id"], "lignes": [{"type_vetement_id": bou["id"], "quantite": 1}]})
    cid = r.json()["id"]
    avant = client.get(f"{P}/statistiques/impayes", headers=headers["admin"]).json()
    assert avant["total"] == 1
    s = client.post(f"{P}/commandes/{cid}/statut", headers=headers["accueil"],
                    json={"statut": "annulee"})
    assert s.status_code == 200, s.text
    apres = client.get(f"{P}/statistiques/impayes", headers=headers["admin"]).json()
    assert apres["total"] == 0
