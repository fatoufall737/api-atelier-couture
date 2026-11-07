"""Initialisation : premier administrateur (.env) + catalogue de départ (annexe B).

Usage : python -m app.seed   (peut être relancé sans risque)
"""
from sqlalchemy import select

from app import security
from app.config import settings
from app.database import SessionLocal
from app.models import TypeVetement, Utilisateur

CATALOGUE = [
    ("Boubou", "Boubou homme en bazin ou brodé", 35_000, 10),
    ("Costume 2 pièces", "Veste et pantalon", 85_000, 14),
    ("Robe", "Robe sur mesure", 30_000, 7),
    ("Ensemble wax", "Tenue deux pièces en wax", 25_000, 7),
    ("Chemise", "Chemise sur mesure", 15_000, 5),
    ("Pantalon", "Pantalon sur mesure", 12_000, 4),
    ("Retouche", "Ourlet, rétrécissement, remplacement de fermeture", 3_000, 2),
]


def main() -> None:
    if not (settings.admin_email and settings.admin_password):
        raise SystemExit("ADMIN_EMAIL et ADMIN_PASSWORD doivent être définis dans le .env")
    email = settings.admin_email.strip().lower()
    with SessionLocal() as db:
        if db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)) is None:
            db.add(
                Utilisateur(
                    email=email,
                    nom_complet=settings.admin_nom_complet,
                    mot_de_passe_hash=security.hasher_mot_de_passe(settings.admin_password),
                    role="admin",
                )
            )
            print(f"Administrateur créé : {email}")
        else:
            print("Administrateur déjà présent")

        for nom, description, prix, delai in CATALOGUE:
            if db.scalar(select(TypeVetement.id).where(TypeVetement.nom == nom)) is None:
                db.add(
                    TypeVetement(nom=nom, description=description, prix_base=prix, delai_jours=delai)
                )
                print(f"Prestation ajoutée : {nom}")
        db.commit()


if __name__ == "__main__":
    main()