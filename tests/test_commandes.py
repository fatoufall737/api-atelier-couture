import pytest

P = "/api/v1"


@pytest.fixture()
def commande(client, headers):
    """Crée un client, 2 prestations et une commande (2 boubous + 1 pantalon, remise 5000)."""
    c = client.post(f"{P}/clients", headers=headers["accueil"],
                    json={"nom": "Diop", "prenom": "Fatou", "telephone": "771234567"})
    assert c.status_code == 201, c.text
    bou = client.post(f"{P}/catalogue", headers=headers["admin"],
                      json={"nom": "Boubou", "prix_base": 35000, "delai_jours": 10}).json()
    pan = client.post(f"{P}/catalogue", headers=headers["admin"],
                      json={"nom": "Pantalon", "prix_base": 12000, "delai_jours": 4}).json()
    r = client.post(f"{P}/commandes", headers=headers["accueil"], json={
        "client_id": c.json()["id"],
        "remise": 5000,
        "lignes": [
            {"type_vetement_id": bou["id"], "quantite": 2},
            {"type_vetement_id": pan["id"], "quantite": 1, "prix_unitaire": 10000},
        ],
    })
    assert r.status_code == 201, r.text
    data = r.json()
    data["_bou"] = bou["id"]
    data["_pan"] = pan["id"]
    return data


def test_rg7_total_calcule_par_le_serveur(commande):
    # 2 x 35000 + 1 x 10000 - 5000 = 75000
    assert commande["montant_total"] == 75000


def test_rg7_modifier_remise_recalcule(client, headers, commande):
    r = client.patch(f"{P}/commandes/{commande['id']}", headers=headers["accueil"], json={"remise": 10000})
    assert r.status_code == 200, r.text
    assert r.json()["montant_total"] == 70000


def test_rg7_remise_superieure_aux_prestations_refusee(client, headers, commande):
    r = client.patch(f"{P}/commandes/{commande['id']}", headers=headers["accueil"], json={"remise": 999999})
    assert r.status_code == 422


def test_tailleur_ne_peut_pas_modifier_commande(client, headers, commande):
    r = client.patch(f"{P}/commandes/{commande['id']}", headers=headers["tailleur"], json={"notes": "x"})
    assert r.status_code == 403


def test_sans_jeton_401(client, commande):
    r = client.patch(f"{P}/commandes/{commande['id']}", json={"notes": "x"})
    assert r.status_code == 401


def test_ajouter_ligne_recalcule(client, headers, commande):
    r = client.post(f"{P}/commandes/{commande['id']}/lignes", headers=headers["accueil"],
                    json={"type_vetement_id": commande["_pan"], "quantite": 1})
    assert r.status_code == 201, r.text
    assert r.json()["montant_total"] == 75000 + 12000  # prix de base par défaut (RG6)


def test_rg6_prestation_inactive_refusee(client, headers, commande):
    client.patch(f"{P}/catalogue/{commande['_pan']}", headers=headers["admin"], json={"actif": False})
    r = client.post(f"{P}/commandes/{commande['id']}/lignes", headers=headers["accueil"],
                    json={"type_vetement_id": commande["_pan"], "quantite": 1})
    assert r.status_code == 422


def test_rg10_retirer_ligne_recalcule(client, headers, commande):
    ligne_id = commande["lignes"][1]["id"]
    r = client.delete(f"{P}/commandes/{commande['id']}/lignes/{ligne_id}", headers=headers["accueil"])
    assert r.status_code == 200, r.text
    assert r.json()["montant_total"] == 65000  # 70000 - 5000


def test_rg10_ligne_inexistante_404(client, headers, commande):
    r = client.delete(f"{P}/commandes/{commande['id']}/lignes/99999", headers=headers["accueil"])
    assert r.status_code == 404


def test_rg10_garde_au_moins_une_ligne(client, headers, commande):
    cid = commande["id"]
    client.patch(f"{P}/commandes/{cid}", headers=headers["accueil"], json={"remise": 0})
    client.delete(f"{P}/commandes/{cid}/lignes/{commande['lignes'][1]['id']}", headers=headers["accueil"])
    r = client.delete(f"{P}/commandes/{cid}/lignes/{commande['lignes'][0]['id']}", headers=headers["accueil"])
    assert r.status_code == 409


def test_rg10_lignes_bloquees_hors_en_attente(client, headers, commande):
    cid = commande["id"]
    s = client.post(f"{P}/commandes/{cid}/statut", headers=headers["accueil"], json={"statut": "en_coupe"})
    assert s.status_code == 200, s.text
    r = client.post(f"{P}/commandes/{cid}/lignes", headers=headers["accueil"],
                    json={"type_vetement_id": commande["_pan"], "quantite": 1})
    assert r.status_code == 409


def test_rg12_commande_annulee_non_modifiable(client, headers, commande):
    cid = commande["id"]
    s = client.post(f"{P}/commandes/{cid}/statut", headers=headers["accueil"], json={"statut": "annulee"})
    assert s.status_code == 200, s.text
    r = client.patch(f"{P}/commandes/{cid}", headers=headers["accueil"], json={"notes": "x"})
    assert r.status_code == 409


def test_rg17_annuler_paiement_recalcule_solde(client, headers, commande):
    cid = commande["id"]
    p = client.post(f"{P}/commandes/{cid}/paiements", headers=headers["accueil"],
                    json={"montant": 20000, "mode": "wave"})
    assert p.status_code == 201, p.text
    liste = client.get(f"{P}/commandes/{cid}/paiements", headers=headers["tailleur"])
    assert liste.status_code == 200 and len(liste.json()) == 1
    pid = liste.json()[0]["id"]

    # l'accueil ne peut pas annuler un paiement
    assert client.delete(f"{P}/paiements/{pid}", headers=headers["accueil"]).status_code == 403
    # l'admin le peut
    assert client.delete(f"{P}/paiements/{pid}", headers=headers["admin"]).status_code == 204

    cmd = client.get(f"{P}/commandes/{cid}", headers=headers["admin"]).json()
    assert cmd["montant_paye"] == 0


def test_annuler_paiement_inconnu_404(client, headers):
    assert client.delete(f"{P}/paiements/99999", headers=headers["admin"]).status_code == 404
