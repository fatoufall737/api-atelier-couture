from datetime import datetime
<<<<<<< HEAD

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

=======
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, maintenant
if TYPE_CHECKING:
    from app.models.commande import Commande
    from app.models.mesure import Mesure
>>>>>>> origin/feature/fondations

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
<<<<<<< HEAD
    # unique=True : deux clients ne peuvent pas avoir le même téléphone
    telephone: Mapped[str] = mapped_column(String(25), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    adresse: Mapped[str | None] = mapped_column(String(255))
    genre: Mapped[str | None] = mapped_column(String(10))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
=======
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
>>>>>>> origin/feature/fondations
