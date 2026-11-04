from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings
from app.database import maintenant

_hasher = PasswordHasher()


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    return _hasher.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_: str) -> bool:
    try:
        return _hasher.verify(hash_, mot_de_passe)
    except (VerificationError, InvalidHashError):
        return False


def creer_jeton(utilisateur_id: int) -> tuple[str, int]:
    """Renvoie (jeton, durée de validité en secondes)."""
    duree = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(utilisateur_id), "exp": maintenant() + duree}
    jeton = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return jeton, int(duree.total_seconds())


def decoder_jeton(jeton: str) -> dict:
    """Lève jwt.PyJWTError si le jeton est invalide ou expiré."""
    return jwt.decode(
        jeton,
        settings.secret_key,
        algorithms=[settings.algorithm],
        options={"require": ["exp", "sub"]},
    )


# Hash factice : permet de toujours vérifier un mot de passe, même si l'e-mail est inconnu (RG23)
HASH_FACTICE = _hasher.hash("mot-de-passe-factice")