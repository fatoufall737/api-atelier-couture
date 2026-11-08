import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import select

from app import security
from app.database import get_db
from app.models import TypeVetement, Utilisateur

CATALOGUE = [
    ("Boubou", "Boubou homme en bazin ou brodé", 35000, 10),
    ("Costume 2 pièces", "Veste et pantalon", 85000, 14),
    ("Robe", "Robe sur mesure", 30000, 7),
    ("Ensemble wax", "Tenue deux pièces en wax", 25000, 7),
    ("Chemise", "Chemise sur mesure", 15000, 5),
    ("Pantalon", "Pantalon sur mesure", 12000, 4),
    ("Retouche", "Ourlet, rétrécissement, remplacement de fermeture", 3000, 2),
]


def main() -> None:
    email = os.getenv("ADMIN_EMAIL")
    mot_de_passe = os.getenv("ADMIN_PASSWORD")
    nom = os.getenv("ADMIN_NOM_COMPLET", "Administrateur")
    if not email or not mot_de_passe:
        raise SystemExit("ADMIN_EMAIL et ADMIN_PASSWORD doivent être définis (.env).")

    db = next(get_db())
    try:
        if db.scalar(select(Utilisateur).where(Utilisateur.email == email)) is None:
            db.add(Utilisateur(
                email=email,
                nom_complet=nom,
                mot_de_passe_hash=security.hasher_mot_de_passe(mot_de_passe),
                role="admin",
                actif=True,
            ))
            print("Admin créé :", email)
        else:
            print("Admin déjà présent :", email)

        for nom_p, description, prix, delai in CATALOGUE:
            if db.scalar(select(TypeVetement).where(TypeVetement.nom == nom_p)) is None:
                db.add(TypeVetement(nom=nom_p, description=description,
                                    prix_base=prix, delai_jours=delai, actif=True))
                print("Prestation ajoutée :", nom_p)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
