import pytest

from app.telephone import normaliser_telephone


@pytest.mark.parametrize(
    "saisie, attendu",
    [
        ("77 123 45 67", "771234567"),
        ("771234567", "771234567"),
        ("(77) 123-45.67", "771234567"),
        ("+221 77 123 45 67", "+221771234567"),
    ],
)
def test_normalisation(saisie, attendu):
    assert normaliser_telephone(saisie) == attendu


@pytest.mark.parametrize("saisie", ["12345", "abc", "77 12 AB 45", "+", "1" * 21, "++22177123456"])
def test_telephone_invalide(saisie):
    with pytest.raises(ValueError):
        normaliser_telephone(saisie)