from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    # Tous les modèles hériteront de cette classe
    pass


def get_db():
    # Ouvre une session pour une requête, puis la ferme toujours
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()