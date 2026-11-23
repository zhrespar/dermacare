"""Build ordered morning/evening routines from already-ranked, already-filtered products.

Respects the manufacturer routine slot (am/pm/both), one product per category per slot,
the step order in rules.ROUTINE_ORDER, and INCOMPATIBLE_PAIRS (a lower-ranked product that
conflicts with an earlier pick in the same slot is skipped and reported).
"""

from __future__ import annotations

from app.schemas.recommendation import ProductIn, RankedProduct, RoutineStep, SkippedStep
from app.services.recommendation import rules


def _conflict(a: set[str], b: set[str], pairs: list[tuple[str, str]]) -> tuple[str, str] | None:
    for x, y in pairs:
        if (x in a and y in b) or (y in a and x in b):
            return (x, y)
    return None


def build_routine(
    slot: str,
    ranked: list[RankedProduct],
    products: dict[str, ProductIn],
    pairs: list[tuple[str, str]] | None = None,
) -> tuple[list[RoutineStep], list[SkippedStep]]:
    pairs = rules.INCOMPATIBLE_PAIRS if pairs is None else pairs
    order = rules.ROUTINE_ORDER[slot]
    chosen: dict[str, RankedProduct] = {}
    skipped: list[SkippedStep] = []
    for r in ranked:  # already sorted best-first
        p = products[r.product_id]
        if r.routine_slot not in (slot, "both") or p.category not in order or p.category in chosen:
            continue
        inci = {i.strip().upper() for i in p.inci}
        clash = None
        for other in chosen.values():
            clash = _conflict(inci, {i.strip().upper() for i in products[other.product_id].inci}, pairs)
            if clash:
                skipped.append(
                    SkippedStep(
                        product_id=r.product_id,
                        reason=f"incompatible_with:{other.product_id}:{'+'.join(clash)}",
                    )
                )
                break
        if not clash:
            chosen[p.category] = r
    steps = [
        RoutineStep(
            step=i + 1,
            category=cat,
            product_id=chosen[cat].product_id,
            usage_instructions=products[chosen[cat].product_id].usage_instructions,
        )
        for i, cat in enumerate(c for c in order if c in chosen)
    ]
    return steps, skipped
