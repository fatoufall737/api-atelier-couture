from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, maintenant
if TYPE_CHECKING:
    from app.models.commande import Commande
    from app.models.mesure import Mesure

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    telephone: Mapped[str] = mapped_column(String(21), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    adresse: Mapped[str | None] = mapped_column(String(255))
    genre: Mapped[str | None] = mapped_column(String(10))  # homme | femme | enfant
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=maintenant, onupdate=maintenant
    )
    mesures: Mapped[list["Mesure"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", order_by="Mesure.date_prise.desc()"
    )
    commandes: Mapped[list["Commande"]] = relationship(back_populates="client")