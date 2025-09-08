from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.nutrition.models import ServingUnit


SUPPORTED_UNITS = {"g", "ml", "unit", "unidad"}


@dataclass
class FactorResult:
    factor: Decimal
    portion_estimated: bool
    serving_unit: ServingUnit


def normalize_unit(unit: str) -> ServingUnit:
    u = (unit or "").strip().lower()
    if u not in SUPPORTED_UNITS:
        raise ValueError("Unsupported unit. Use one of: g, ml, unidad")
    if u == "unidad":
        return ServingUnit.unit
    if u == "unit":
        return ServingUnit.unit
    if u == "g":
        return ServingUnit.g
    return ServingUnit.ml


def compute_factor(
    quantity: Decimal | float | int,
    unit: str,
    unit_weight_grams: Optional[Decimal | float | int] = None,
) -> FactorResult:
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, TypeError):
        raise ValueError("quantity must be a number > 0")
    if qty <= 0:
        raise ValueError("quantity must be > 0")

    su = normalize_unit(unit)

    if su in {ServingUnit.g, ServingUnit.ml}:
        # MVP: assume 1 g/ml density equivalence for ml
        factor = (qty / Decimal("100"))
        return FactorResult(factor=factor.quantize(Decimal("0.0001")), portion_estimated=False, serving_unit=su)

    # su == unit
    if unit_weight_grams is not None:
        uw = Decimal(str(unit_weight_grams))
        if uw <= 0:
            raise ValueError("unit_weight_grams must be > 0 when provided")
        factor = (qty * uw) / Decimal("100")
        return FactorResult(factor=factor.quantize(Decimal("0.0001")), portion_estimated=False, serving_unit=su)

    # Fallback: treat 1 unit as 100 g
    factor = qty  # qty * (100/100)
    return FactorResult(factor=Decimal(factor).quantize(Decimal("0.0001")), portion_estimated=True, serving_unit=su)

