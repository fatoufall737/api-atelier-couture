from datetime import date
from uuid import uuid4

CORPS = {"tour_taille": 80, "tour_poitrine": 95}


def creer_client(client, headers):
    # Un téléphone différent à chaque appel, pour éviter le doublon (RG1)
    telephone = "77" + str(uuid4().int)[:7]
    reponse = client.post(
        "/api/v1/clients",
        json={"nom": "Diop", "prenom": "Fatou", "telephone": telephone},
        headers=headers["accueil"],
    )
    assert reponse.status_code == 201
    return reponse.json()["id"]


def test_tailleur_enregistre_des_mesures(client, headers):
    client_id = creer_client(client, headers)
    reponse = client.post(
        f"/api/v1/clients/{client_id}/mesures",
        json=CORPS,
        headers=headers["tailleur"],
    )
    assert reponse.status_code == 201
    donnees = reponse.json()
    assert donnees["date_prise"] == date.today().isoformat()
    assert donnees["tour_taille"] == 80
    assert donnees["prise_par_id"] is not None


def test_accueil_ne_peut_pas_prendre_de_mesures(client, headers):
    client_id = creer_client(client, headers)
    reponse = client.post(
        f"/api/v1/clients/{client_id}/mesures",
        json=CORPS,
        headers=headers["accueil"],
    )
    assert reponse.status_code == 403


def test_rg2_prise_vide_refusee(client, headers):
    client_id = creer_client(client, headers)
    reponse = client.post(
        f"/api/v1/clients/{client_id}/mesures",
        json={},
        headers=headers["tailleur"],
    )
    assert reponse.status_code == 422
    assert "detail" in reponse.json()


def test_rg2_mesure_hors_limites_refusee(client, headers):
    client_id = creer_client(client, headers)
    for valeur in (0, -5, 301):
        reponse = client.post(
            f"/api/v1/clients/{client_id}/mesures",
            json={"tour_taille": valeur},
            headers=headers["tailleur"],
        )
        assert reponse.status_code == 422


def test_rg3_derniere_mesure_choisie_par_date(client, headers):
    client_id = creer_client(client, headers)
    url = f"/api/v1/clients/{client_id}/mesures"
    # Saisie en premier, mais la plus récente par sa date
    client.post(
        url,
        json={"tour_taille": 80, "date_prise": "2026-03-01"},
        headers=headers["tailleur"],
    )
    # Saisie en second, mais la plus ancienne par sa date
    client.post(
        url,
        json={"tour_taille": 70, "date_prise": "2026-01-01"},
        headers=headers["tailleur"],
    )
    reponse = client.get(f"{url}/derniere", headers=headers["accueil"])
    assert reponse.status_code == 200
    assert reponse.json()["tour_taille"] == 80


def test_derniere_mesure_404_sans_mesures(client, headers):
    client_id = creer_client(client, headers)
    reponse = client.get(
        f"/api/v1/clients/{client_id}/mesures/derniere",
        headers=headers["accueil"],
    )
    assert reponse.status_code == 404


def test_correction_ne_peut_pas_tout_supprimer(client, headers):
    client_id = creer_client(client, headers)
    creation = client.post(
        f"/api/v1/clients/{client_id}/mesures",
        json={"tour_taille": 80},
        headers=headers["tailleur"],
    )
    mesure_id = creation.json()["id"]
    reponse = client.patch(
        f"/api/v1/mesures/{mesure_id}",
        json={"tour_taille": None},
        headers=headers["tailleur"],
    )
    assert reponse.status_code == 422


def test_tailleur_supprime_une_prise_de_mesures(client, headers):
    client_id = creer_client(client, headers)
    creation = client.post(
        f"/api/v1/clients/{client_id}/mesures",
        json=CORPS,
        headers=headers["tailleur"],
    )
    mesure_id = creation.json()["id"]
    reponse = client.delete(
        f"/api/v1/mesures/{mesure_id}",
        headers=headers["tailleur"],
    )
    assert reponse.status_code == 204