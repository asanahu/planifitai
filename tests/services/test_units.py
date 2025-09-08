from decimal import Decimal

from services.units import compute_factor


def test_factor_for_grams_150g():
    fr = compute_factor(Decimal("150"), "g")
    assert fr.factor == Decimal("1.5000")
    assert fr.portion_estimated is False


def test_factor_for_ml_200ml():
    fr = compute_factor(Decimal("200"), "ml")
    assert fr.factor == Decimal("2.0000")
    assert fr.portion_estimated is False


def test_factor_for_unit_with_known_weight():
    fr = compute_factor(1, "unit", unit_weight_grams=120)
    assert fr.factor == Decimal("1.2000")
    assert fr.portion_estimated is False


def test_factor_for_unidad_without_known_weight():
    fr = compute_factor(2, "unidad")
    assert fr.factor == Decimal("2.0000")
    assert fr.portion_estimated is True
