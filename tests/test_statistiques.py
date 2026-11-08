STATUTS = [
    "en_attente",
    "en_coupe",
    "en_couture",
    "essayage",
    "retouches",
    "terminee",
    "livree",
    "annulee",
]

URL = "/api/v1/statistiques/tableau-de-bord"
URL_CA = "/api/v1/statistiques/chiffre-affaires"


def test_admin_voit_le_tableau_de_bord(client, headers):
    reponse = client.get(URL, headers=headers["admin"])
    assert reponse.status_code == 200
    donnees = reponse.json()
    for cle in (
        "chiffre_affaires_mois",
        "encaisse_mois",
        "nb_commandes_mois",
        "reste_a_encaisser",
        "commandes_par_statut",
        "nb_commandes_en_retard",
        "commandes_pretes_a_livrer",
        "livraisons_du_jour",
    ):
        assert cle in donnees
        if cle != "commandes_par_statut":
            assert donnees[cle] >= 0


def test_tous_les_statuts_sont_presents_meme_a_zero(client, headers):
    reponse = client.get(URL, headers=headers["admin"])
    assert set(reponse.json()["commandes_par_statut"]) == set(STATUTS)


def test_accueil_ne_voit_pas_les_statistiques(client, headers):
    reponse = client.get(URL, headers=headers["accueil"])
    assert reponse.status_code == 403


def test_tailleur_ne_voit_pas_les_statistiques(client, headers):
    reponse = client.get(URL, headers=headers["tailleur"])
    assert reponse.status_code == 403


def test_statistiques_sans_jeton_refusees(client):
    reponse = client.get(URL)
    assert reponse.status_code == 401


def test_chiffre_affaires_par_defaut(client, headers):
    reponse = client.get(URL_CA, headers=headers["admin"])
    assert reponse.status_code == 200
    assert isinstance(reponse.json(), list)


def test_chiffre_affaires_periode_sans_activite_est_vide(client, headers):
    # Seules les périodes avec activité sont listées
    reponse = client.get(
        URL_CA,
        params={
            "granularite": "mois",
            "date_debut": "2000-01-01",
            "date_fin": "2000-12-31",
        },
        headers=headers["admin"],
    )
    assert reponse.status_code == 200
    assert reponse.json() == []


def test_chiffre_affaires_dates_inversees_refusees(client, headers):
    reponse = client.get(
        URL_CA,
        params={"date_debut": "2026-12-31", "date_fin": "2026-01-01"},
        headers=headers["admin"],
    )
    assert reponse.status_code == 422
    assert "detail" in reponse.json()


def test_chiffre_affaires_granularite_invalide_refusee(client, headers):
    reponse = client.get(
        URL_CA, params={"granularite": "semaine"}, headers=headers["admin"]
    )
    assert reponse.status_code == 422


def test_chiffre_affaires_reserve_a_l_admin(client, headers):
    assert client.get(URL_CA, headers=headers["accueil"]).status_code == 403
    assert client.get(URL_CA, headers=headers["tailleur"]).status_code == 403
    assert client.get(URL_CA).status_code == 401