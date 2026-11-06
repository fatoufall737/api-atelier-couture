from app import security
from tests.conftest import MOT_DE_PASSE

API = "/api/v1"


def test_login_ok(client, creer_utilisateur):
    u = creer_utilisateur("accueil")
    r = client.post(f"{API}/auth/login", data={"username": u.email, "password": MOT_DE_PASSE})
    assert r.status_code == 200
    corps = r.json()
    assert corps["token_type"] == "bearer" and corps["expires_in"] > 0 and corps["access_token"]


def test_rg23_meme_message_email_inconnu_ou_mauvais_mot_de_passe(client, creer_utilisateur):
    u = creer_utilisateur("accueil")
    r1 = client.post(f"{API}/auth/login", data={"username": u.email, "password": "faux-faux-faux"})
    r2 = client.post(f"{API}/auth/login", data={"username": "inconnu@atelier.sn", "password": "faux-faux-faux"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


def test_compte_desactive_refuse_au_login(client, creer_utilisateur):
    u = creer_utilisateur("accueil", actif=False)
    r = client.post(f"{API}/auth/login", data={"username": u.email, "password": MOT_DE_PASSE})
    assert r.status_code == 401


def test_rg22_compte_desactive_refuse_avec_jeton_valide(client, headers):
    liste = client.get(f"{API}/utilisateurs", headers=headers["admin"]).json()
    accueil = next(u for u in liste if u["role"] == "accueil")
    assert client.get(f"{API}/auth/me", headers=headers["accueil"]).status_code == 200
    client.patch(f"{API}/utilisateurs/{accueil['id']}", json={"actif": False}, headers=headers["admin"])
    assert client.get(f"{API}/auth/me", headers=headers["accueil"]).status_code == 401


def test_sans_jeton_ou_jeton_invalide_401(client):
    assert client.get(f"{API}/auth/me").status_code == 401
    r = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer nimportequoi"})
    assert r.status_code == 401


def test_jeton_expire_401(client, creer_utilisateur, monkeypatch):
    u = creer_utilisateur("accueil")
    monkeypatch.setattr(security.settings, "access_token_expire_minutes", -1)
    jeton, _ = security.creer_jeton(u.id)
    r = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {jeton}"})
    assert r.status_code == 401


def test_me_ne_renvoie_aucune_donnee_sensible(client, headers):
    corps = client.get(f"{API}/auth/me", headers=headers["accueil"]).json()
    assert "mot_de_passe" not in corps and "mot_de_passe_hash" not in corps


def test_rg21_mot_de_passe_hache_argon2(session_factory, creer_utilisateur):
    from app.models import Utilisateur

    u = creer_utilisateur("accueil")
    with session_factory() as db:
        hash_ = db.get(Utilisateur, u.id).mot_de_passe_hash
    assert hash_.startswith("$argon2") and MOT_DE_PASSE not in hash_