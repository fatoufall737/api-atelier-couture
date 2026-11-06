"""Test des droits par rôle (section 4 du sujet) : une seule matrice pour toutes les routes.

Pour chaque route : les rôles autorisés ne reçoivent ni 401 ni 403, les autres reçoivent 403,
et sans jeton on reçoit 401. L'admin est toujours autorisé. À compléter à chaque nouvelle route.
"""
import pytest

API = "/api/v1"
TOUS = {"admin", "accueil", "tailleur"}
ADMIN = {"admin"}

ROUTES = [
    ("GET", "/auth/me", TOUS),
    ("POST", "/utilisateurs", ADMIN),
    ("GET", "/utilisateurs", ADMIN),
    ("GET", "/utilisateurs/1", ADMIN),
    ("PATCH", "/utilisateurs/1", ADMIN),
    ("POST", "/clients", TOUS),
    ("GET", "/clients", TOUS),
    ("GET", "/clients/1", TOUS),
    ("PATCH", "/clients/1", TOUS),
    ("DELETE", "/clients/1", ADMIN),
    ("POST", "/catalogue", ADMIN),
    ("GET", "/catalogue", TOUS),
    ("GET", "/catalogue/1", TOUS),
    ("PATCH", "/catalogue/1", ADMIN),
]


@pytest.mark.parametrize("methode, chemin, autorises", ROUTES)
def test_droits_par_role(client, headers, methode, chemin, autorises):
    url = f"{API}{chemin}"
    for role in ("admin", "accueil", "tailleur"):
        r = client.request(methode, url, json={}, headers=headers[role])
        if role in autorises:
            assert r.status_code not in (401, 403), f"{role} devrait pouvoir faire {methode} {chemin}"
        else:
            assert r.status_code == 403, f"{role} ne devrait pas pouvoir faire {methode} {chemin}"
    assert client.request(methode, url, json={}).status_code == 401