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