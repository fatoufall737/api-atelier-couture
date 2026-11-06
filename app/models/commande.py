from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, maintenant
from app.models.catalogue import TypeVetement
from app.models.client import Client
from app.models.mesure import Mesure


class Commande(Base):
    __tablename__ = "commandes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # RG5 : CMD-AAAA-NNNNN. Le numéro dépend de l'id, qui n'existe qu'après l'insertion :
    # le service insère avec une valeur temporaire unique, fait un flush, puis écrit le vrai numéro.
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    mesure_id: Mapped[int | None] = mapped_column(ForeignKey("mesures.id"))
    statut: Mapped[str] = mapped_column(String(20), default="en_attente", index=True)
    date_commande: Mapped[date] = mapped_column(Date, default=date.today)
    date_livraison_prevue: Mapped[date] = mapped_column(Date)
    date_livraison_reelle: Mapped[date | None] = mapped_column(Date)
    remise: Mapped[int] = mapped_column(default=0)
    montant_total: Mapped[int] = mapped_column(default=0)
    montant_paye: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    cree_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=maintenant, onupdate=maintenant
    )

    client: Mapped[Client] = relationship(back_populates="commandes")
    mesure: Mapped[Mesure | None] = relationship()
    lignes: Mapped[list["LigneCommande"]] = relationship(
        back_populates="commande", cascade="all, delete-orphan", order_by="LigneCommande.id"
    )
    paiements: Mapped[list["Paiement"]] = relationship(
        back_populates="commande", cascade="all, delete-orphan", order_by="Paiement.id"
    )
    historique: Mapped[list["HistoriqueStatut"]] = relationship(
        back_populates="commande", cascade="all, delete-orphan", order_by="HistoriqueStatut.id"
    )
    livraison: Mapped["Livraison | None"] = relationship(
        back_populates="commande", cascade="all, delete-orphan", uselist=False
    )

    @property
    def solde(self) -> int:
        return self.montant_total - self.montant_paye


class LigneCommande(Base):
    __tablename__ = "lignes_commande"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    type_vetement_id: Mapped[int] = mapped_column(ForeignKey("types_vetement.id"))
    description: Mapped[str | None] = mapped_column(Text)
    quantite: Mapped[int]
    prix_unitaire: Mapped[int]

    commande: Mapped[Commande] = relationship(back_populates="lignes")
    type_vetement: Mapped[TypeVetement] = relationship()


class HistoriqueStatut(Base):
    __tablename__ = "historique_statuts"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    ancien_statut: Mapped[str | None] = mapped_column(String(20))  # vide à la création
    nouveau_statut: Mapped[str] = mapped_column(String(20))
    commentaire: Mapped[str | None] = mapped_column(Text)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    date_changement: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)

    commande: Mapped[Commande] = relationship(back_populates="historique")


class Paiement(Base):
    __tablename__ = "paiements"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    montant: Mapped[int]
    mode: Mapped[str] = mapped_column(String(20))  # especes | wave | orange_money | virement | cheque
    reference: Mapped[str | None] = mapped_column(String(100))
    date_paiement: Mapped[date] = mapped_column(Date, default=date.today)
    enregistre_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)

    commande: Mapped[Commande] = relationship(back_populates="paiements")


class Livraison(Base):
    __tablename__ = "livraisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), unique=True
    )
    mode: Mapped[str] = mapped_column(String(20))  # retrait_atelier | domicile
    adresse: Mapped[str | None] = mapped_column(String(255))
    livreur: Mapped[str | None] = mapped_column(String(100))
    date_prevue: Mapped[date] = mapped_column(Date)
    date_effective: Mapped[date | None] = mapped_column(Date)
    statut: Mapped[str] = mapped_column(String(20), default="planifiee")  # planifiee | livree
    notes: Mapped[str | None] = mapped_column(Text)

    commande: Mapped[Commande] = relationship(back_populates="livraison")