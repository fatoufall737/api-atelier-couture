from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, maintenant

if TYPE_CHECKING:
    from app.models.client import Client

# Les 18 mesures facultatives (en cm). Votre amie s'en servira pour la règle RG2.
CHAMPS_MESURES = (
    "taille_cm", "tour_cou", "carrure_dos", "longueur_epaule", "tour_poitrine",
    "tour_taille", "tour_bassin", "longueur_manche", "tour_bras", "tour_poignet",
    "longueur_dos", "longueur_haut", "longueur_pantalon", "tour_cuisse", "tour_genou",
    "bas_pantalon", "entrejambe", "longueur_robe",
)


class Mesure(Base):
    __tablename__ = "mesures"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    date_prise: Mapped[date] = mapped_column(Date, default=date.today)
    prise_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    notes: Mapped[str | None] = mapped_column(Text)

    taille_cm: Mapped[float | None]
    tour_cou: Mapped[float | None]
    carrure_dos: Mapped[float | None]
    longueur_epaule: Mapped[float | None]
    tour_poitrine: Mapped[float | None]
    tour_taille: Mapped[float | None]
    tour_bassin: Mapped[float | None]
    longueur_manche: Mapped[float | None]
    tour_bras: Mapped[float | None]
    tour_poignet: Mapped[float | None]
    longueur_dos: Mapped[float | None]
    longueur_haut: Mapped[float | None]
    longueur_pantalon: Mapped[float | None]
    tour_cuisse: Mapped[float | None]
    tour_genou: Mapped[float | None]
    bas_pantalon: Mapped[float | None]
    entrejambe: Mapped[float | None]
    longueur_robe: Mapped[float | None]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)

    client: Mapped["Client"] = relationship(back_populates="mesures")