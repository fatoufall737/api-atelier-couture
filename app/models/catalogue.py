from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TypeVetement(Base):
    __tablename__ = "types_vetement"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    prix_base: Mapped[int]      # en FCFA, entier
    delai_jours: Mapped[int]
    actif: Mapped[bool] = mapped_column(default=True)