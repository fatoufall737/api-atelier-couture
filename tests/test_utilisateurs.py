API = "/api/v1"
NOUVEAU = {
    "email": "Fatou@Atelier.sn",
    "nom_complet": "Fatou Sow",
    "mot_de_passe": "unmotdepasse",
    "role": "tailleur",
}


def test_creation_201_sans_hash_et_email_normalise(client, headers):
    r = client.post(f"{API}/utilisateurs", json=NOUVEAU, headers=headers["admin"])
    assert r.status_code == 201
    corps = r.json()
    assert corps["email"] == "fatou@atelier.sn"
    assert "mot_de_passe" not in corps and "mot_de_passe_hash" not in corps


def test_email_en_double_409(client, headers):
    client.post(f"{API}/utilisateurs", json=NOUVEAU, headers=headers["admin"])
    r = client.post(
        f"{API}/utilisateurs", json={**NOUVEAU, "email": "fatou@atelier.sn"}, headers=headers["admin"]
    )
    assert r.status_code == 409


def test_rg21_mot_de_passe_trop_court_422(client, headers):
    r = client.post(
        f"{API}/utilisateurs", json={**NOUVEAU, "mot_de_passe": "court"}, headers=headers["admin"]
    )
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)


def test_liste_triee_par_nom_et_detail_404(client, headers):
    noms = [u["nom_complet"] for u in client.get(f"{API}/utilisateurs", headers=headers["admin"]).json()]
    assert noms == sorted(noms)
    assert client.get(f"{API}/utilisateurs/9999", headers=headers["admin"]).status_code == 404


def test_rg24_admin_ne_peut_pas_se_desactiver_ni_se_retrograder(client, headers):
    moi = client.get(f"{API}/auth/me", headers=headers["admin"]).json()
    url = f"{API}/utilisateurs/{moi['id']}"
    assert client.patch(url, json={"actif": False}, headers=headers["admin"]).status_code == 409
    assert client.patch(url, json={"role": "accueil"}, headers=headers["admin"]).status_code == 409
    assert client.patch(url, json={"nom_complet": "Nouveau nom"}, headers=headers["admin"]).status_code == 200


def test_patch_changement_de_mot_de_passe(client, headers, se_connecter):
    cree = client.post(f"{API}/utilisateurs", json=NOUVEAU, headers=headers["admin"]).json()
    client.patch(
        f"{API}/utilisateurs/{cree['id']}",
        json={"mot_de_passe": "nouveaumotdepasse"},
        headers=headers["admin"],
    )
    se_connecter("fatou@atelier.sn", "nouveaumotdepasse")  # échoue si le mot de passe n'a pas changé


def test_admin_peut_desactiver_un_autre_compte(client, headers):
    liste = client.get(f"{API}/utilisateurs", headers=headers["admin"]).json()
    tailleur = next(u for u in liste if u["role"] == "tailleur")
    r = client.patch(f"{API}/utilisateurs/{tailleur['id']}", json={"actif": False}, headers=headers["admin"])
    assert r.status_code == 200 and r.json()["actif"] is False