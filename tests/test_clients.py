API = "/api/v1"
FATOU = {"nom": "Diop", "prenom": "Fatou", "telephone": "77 123 45 67", "genre": "femme"}


def creer(client, headers, **extra):
    return client.post(f"{API}/clients", json={**FATOU, **extra}, headers=headers["accueil"])


def test_creation_normalise_le_telephone(client, headers):
    r = creer(client, headers)
    assert r.status_code == 201
    assert r.json()["telephone"] == "771234567"


def test_rg1_doublon_apres_normalisation_409(client, headers):
    creer(client, headers)
    r = creer(client, headers, prenom="Autre", telephone="771234567")
    assert r.status_code == 409


def test_telephone_invalide_422(client, headers):
    r = creer(client, headers, telephone="12ab")
    assert r.status_code == 422 and isinstance(r.json()["detail"], str)


def test_tous_les_roles_peuvent_creer_et_lire(client, headers):
    for i, role in enumerate(("accueil", "tailleur", "admin")):
        r = client.post(
            f"{API}/clients", json={**FATOU, "telephone": f"7700000{i}0"}, headers=headers[role]
        )
        assert r.status_code == 201
    assert client.get(f"{API}/clients", headers=headers["tailleur"]).status_code == 200


def test_detail_404(client, headers):
    assert client.get(f"{API}/clients/999", headers=headers["accueil"]).status_code == 404


def test_patch_partiel_ne_change_que_les_champs_envoyes(client, headers):
    c = creer(client, headers).json()
    r = client.patch(f"{API}/clients/{c['id']}", json={"adresse": "Médina"}, headers=headers["accueil"])
    assert r.status_code == 200
    assert r.json()["adresse"] == "Médina" and r.json()["nom"] == "Diop"


def test_patch_champs_obligatoires_non_videables_422(client, headers):
    c = creer(client, headers).json()
    for champ in ("nom", "prenom", "telephone"):
        r = client.patch(f"{API}/clients/{c['id']}", json={champ: None}, headers=headers["accueil"])
        assert r.status_code == 422, champ


def test_patch_garder_son_numero_ok_prendre_celui_dun_autre_409(client, headers):
    c1 = creer(client, headers).json()
    creer(client, headers, telephone="76 000 00 00")
    url1 = f"{API}/clients/{c1['id']}"
    assert client.patch(url1, json={"telephone": "77-123-45-67"}, headers=headers["accueil"]).status_code == 200
    assert client.patch(url1, json={"telephone": "760000000"}, headers=headers["accueil"]).status_code == 409


def test_suppression_reservee_a_ladmin(client, headers):
    c = creer(client, headers).json()
    url = f"{API}/clients/{c['id']}"
    assert client.delete(url, headers=headers["accueil"]).status_code == 403
    assert client.delete(url, headers=headers["tailleur"]).status_code == 403
    assert client.delete(url, headers=headers["admin"]).status_code == 204
    assert client.get(url, headers=headers["admin"]).status_code == 404


def test_liste_paginee_triee_et_filtres(client, headers):
    for nom, prenom, tel, genre in [
        ("Sow", "Awa", "770000001", "femme"),
        ("Ba", "Moussa", "770000002", "homme"),
        ("Ba", "Aminata", "770000003", "femme"),
    ]:
        client.post(
            f"{API}/clients",
            json={"nom": nom, "prenom": prenom, "telephone": tel, "genre": genre},
            headers=headers["accueil"],
        )
    h = headers["accueil"]
    page = client.get(f"{API}/clients", headers=h).json()
    assert page["total"] == 3 and page["limit"] == 20 and page["offset"] == 0
    assert [(c["nom"], c["prenom"]) for c in page["items"]] == [
        ("Ba", "Aminata"), ("Ba", "Moussa"), ("Sow", "Awa"),
    ]
    assert client.get(f"{API}/clients?limit=1&offset=1", headers=h).json()["items"][0]["prenom"] == "Moussa"
    assert client.get(f"{API}/clients?genre=homme", headers=h).json()["total"] == 1
    assert client.get(f"{API}/clients?q=ba", headers=h).json()["total"] == 2
    assert client.get(f"{API}/clients?q=7700000", headers=h).json()["total"] == 3
    assert client.get(f"{API}/clients?q=a", headers=h).status_code == 422
    assert client.get(f"{API}/clients?limit=101", headers=h).status_code == 422


def test_rg4_client_avec_commandes_non_supprimable(client, headers, inserer_commande):
    cid = creer(client, headers).json()["id"]
    moi = client.get(f"{API}/auth/me", headers=headers["accueil"]).json()
    inserer_commande(cid, moi["id"])
    assert client.delete(f"{API}/clients/{cid}", headers=headers["admin"]).status_code == 409
    assert client.get(f"{API}/clients/{cid}", headers=headers["admin"]).status_code == 200