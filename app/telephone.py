import re

_SEPARATEURS = re.compile(r"[\s.\-()]")
_FORME_VALIDE = re.compile(r"^\+?\d{6,20}$")


def normaliser_telephone(valeur: str) -> str:
    """RG1 : supprime espaces, points, tirets, parenthèses, puis vérifie la forme."""
    nettoye = _SEPARATEURS.sub("", valeur)
    if not _FORME_VALIDE.match(nettoye):
        raise ValueError(
            "Numéro de téléphone invalide : 6 à 20 chiffres, avec un « + » initial facultatif"
        )
    return nettoye