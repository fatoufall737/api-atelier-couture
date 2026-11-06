API = "/api/v1"
BOUBOU = {"nom": "Boubou", "description": "Boubou homme", "prix_base": 35000, "delai_jours": 10}


def test_creation_reservee_a_ladmin(client, headers):
    assert client.post(f"{API}/catalogue", json=BOUBOU, headers=headers["accueil"]).status_code == 403
    assert client.post(f"{API}/catalogue", json=BOUBOU, headers=headers["tailleur"]).status_code == 403
    r = client.post(f"{API}/catalogue", json=BOUBOU, headers=headers["admin"])
    assert r.status_code == 201 and r.json()["actif"] is True


def test_nom_unique_409(client, headers):
    client.post(f"{API}/catalogue", json=BOUBOU, headers=headers["admin"])
    assert client.post(f"{API}/catalogue", json=BOUBOU, headers=headers["admin"]).status_code == 409


def test_valeurs_invalides_422(client, headers):
    for mauvais in ({"prix_base": -1}, {"delai_jours": 0}, {"prix_base": "beaucoup"}):
        r = client.post(f"{API}/catalogue", json={**BOUBOU, "nom": "X", **mauvais}, headers=headers["admin"])
        assert r.status_code == 422


def test_liste_actifs_seulement_par_defaut_et_tri(client, headers):
    for nom in ("Robe", "Chemise", "Boubou"):
        client.post(f"{API}/catalogue", json={**BOUBOU, "nom": nom}, headers=headers["admin"])
    robe = next(p for p in client.get(f"{API}/catalogue", headers=headers["tailleur"]).json() if p["nom"] == "Robe")
    client.patch(f"{API}/catalogue/{robe['id']}", json={"actif": False}, headers=headers["admin"])
    noms = [p["nom"] for p in client.get(f"{API}/catalogue", headers=headers["tailleur"]).json()]
    assert noms == ["Boubou", "Chemise"]
    tous = [
        p["nom"]
        for p in client.get(f"{API}/catalogue?actifs_seulement=false", headers=headers["tailleur"]).json()
    ]
    assert tous == ["Boubou", "Chemise", "Robe"]


def test_detail_404_et_patch(client, headers):
    assert client.get(f"{API}/catalogue/999", headers=headers["accueil"]).status_code == 404
    cree = client.post(f"{API}/catalogue", json=BOUBOU, headers=headers["admin"]).json()
    url = f"{API}/catalogue/{cree['id']}"
    assert client.patch(url, json={"prix_base": 40000}, headers=headers["accueil"]).status_code == 403
    r = client.patch(url, json={"prix_base": 40000}, headers=headers["admin"])
    assert r.status_code == 200 and r.json()["prix_base"] == 40000 and r.json()["nom"] == "Boubou"
    assert client.patch(f"{API}/catalogue/999", json={"prix_base": 1}, headers=headers["admin"]).status_code == 404