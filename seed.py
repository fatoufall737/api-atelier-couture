"""Initialisation : crée le premier administrateur à partir du .env.

Usage : python -m app.seed   (peut être relancé sans risque)
"""
from sqlalchemy import select

from app import security
from app.config import settings
from app.database import SessionLocal
from app.models import Utilisateur


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
        db.commit()


if __name__ == "__main__":
    main()