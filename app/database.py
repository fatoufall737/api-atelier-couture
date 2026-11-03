from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

<<<<<<< HEAD
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    # Tous les modèles hériteront de cette classe
=======
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
>>>>>>> feature/fondations
    pass


def get_db():
<<<<<<< HEAD
    # Ouvre une session pour une requête, puis la ferme toujours
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
=======
    with SessionLocal() as db:
        yield db
>>>>>>> feature/fondations
