import os

# Variables de test, définies AVANT l'import de l'application : elles passent devant le .env,
# donc les tests ne touchent jamais votre vraie base PostgreSQL.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_unused.db")
os.environ.setdefault("SECRET_KEY", "cle-de-test-uniquement-pas-pour-la-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import security
from app.database import Base, get_db
from app.main import app
from app.models import Utilisateur

MOT_DE_PASSE = "MotDePasse123"


@pytest.fixture()
def session_factory():
    # SQLite en mémoire : une base neuve et vide pour chaque test
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    def _get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def creer_utilisateur(session_factory):
    def _creer(role: str, email: str | None = None, actif: bool = True) -> Utilisateur:
        with session_factory() as db:
            u = Utilisateur(
                email=email or f"{role}@atelier.sn",
                nom_complet=f"Test {role}",
                mot_de_passe_hash=security.hasher_mot_de_passe(MOT_DE_PASSE),
                role=role,
                actif=actif,
            )
            db.add(u)
            db.commit()
            return u

    return _creer


@pytest.fixture()
def se_connecter(client):
    def _login(email: str, mot_de_passe: str = MOT_DE_PASSE) -> dict:
        r = client.post("/api/v1/auth/login", data={"username": email, "password": mot_de_passe})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _login


@pytest.fixture()
def headers(creer_utilisateur, se_connecter):
    """En-têtes d'authentification par rôle : headers['admin'], headers['accueil']..."""
    resultat = {}
    for role in ("admin", "accueil", "tailleur"):
        u = creer_utilisateur(role)
        resultat[role] = se_connecter(u.email)
    return resultat
@pytest.fixture()
def inserer_commande(session_factory):
    """Insère directement une commande minimale (sans passer par l'API)."""
    from datetime import date

    from app.models import Commande

    def _inserer(client_id: int, cree_par_id: int, mesure_id: int | None = None) -> int:
        with session_factory() as db:
            cmd = Commande(
                numero=f"TEMP-{client_id}-{mesure_id}",
                client_id=client_id,
                mesure_id=mesure_id,
                date_livraison_prevue=date(2026, 12, 1),
                cree_par_id=cree_par_id,
            )
            db.add(cmd)
            db.commit()
            return cmd.id

    return _inserer