"""Product catalog: load a catalog version for the engine, and import curated CSV rows.

List fields use ";" as separator (INCI names may contain commas, e.g. 1,2-HEXANEDIOL).
Only rows with verification_status == "verified" and every required field are imported.
Open Beauty Facts may appear only as `discovery_url`; `source_url` must be the authoritative
(manufacturer / package) source. Nothing here creates product data on its own.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CatalogVersion, Ingredient, Product, ProductIngredient
from app.schemas.recommendation import ProductIn

REQUIRED = (
    "brand", "name", "category", "routine_slot", "inci_full", "source_url", "source_type",
    "accessed_at", "verified_at", "verification_status",
)  # fmt: skip
CATEGORIES = {"cleanser", "treatment", "serum", "eye", "moisturizer", "sunscreen"}
SLOTS = {"am", "pm", "both"}
SOURCE_TYPES = {"manufacturer", "package"}
NEEDS = {"acne_care", "wrinkle_care", "under_eye_care", "hydration", "sun_protection"}
SKIN_TYPES = {"dry", "oily", "combination", "normal"}


@dataclass
class ImportReport:
    imported: int = 0
    rejected: list[tuple[int, str, list[str]]] = field(default_factory=list)  # (csv line, name, reasons)


def _split(v: str | None, sep: str = ",") -> list[str]:
    return [x.strip() for x in (v or "").split(sep) if x.strip()]


def _date(v: str) -> datetime:
    return datetime.fromisoformat(v.strip())


def validate_row(r: dict[str, str]) -> list[str]:
    errs = [f"missing:{k}" for k in REQUIRED if not (r.get(k) or "").strip()]
    if errs:
        return errs
    if r["verification_status"].strip() != "verified":
        errs.append("not_verified")
    if r["category"].strip() not in CATEGORIES:
        errs.append("bad_category")
    if r["routine_slot"].strip() not in SLOTS:
        errs.append("bad_routine_slot")
    if r["source_type"].strip() not in SOURCE_TYPES:
        errs.append("source_must_be_manufacturer_or_package")
    if "openbeautyfacts" in r["source_url"].lower():
        errs.append("open_beauty_facts_is_discovery_only")
    if not r["source_url"].strip().startswith(("http://", "https://")):
        errs.append("bad_source_url")
    if set(_split(r.get("targets"), ";")) - NEEDS:
        errs.append("bad_targets")
    if set(_split(r.get("suitable_skin_types"), ";")) - SKIN_TYPES:
        errs.append("bad_skin_types")
    inci = {i.upper() for i in _split(r["inci_full"], ";")}
    if not inci:
        errs.append("empty_inci")
    if {k.upper() for k in _split(r.get("key_ingredients"), ";")} - inci:
        errs.append("key_ingredient_not_in_inci")
    for k in ("accessed_at", "verified_at"):
        try:
            _date(r[k])
        except ValueError:
            errs.append(f"bad_date:{k}")
    if (r.get("price") or "").strip():
        try:
            if float(r["price"]) < 0:
                errs.append("bad_price")
        except ValueError:
            errs.append("bad_price")
    return errs


def import_csv(db: Session, path: Path, version_label: str, freeze: bool = False) -> ImportReport:
    version = db.scalar(select(CatalogVersion).where(CatalogVersion.label == version_label))
    if version is None:
        version = CatalogVersion(label=version_label, frozen=False)
        db.add(version)
        db.flush()
    if version.frozen:
        raise ValueError(f"catalog version {version_label} is frozen")
    rep = ImportReport()
    ingredients = {i.inci_name: i for i in db.scalars(select(Ingredient))}
    with path.open(newline="", encoding="utf-8") as fh:
        for line, r in enumerate(csv.DictReader(fh), start=2):
            errs = validate_row(r)
            if errs:
                rep.rejected.append((line, r.get("name") or "", errs))
                continue
            key = {k.upper() for k in _split(r.get("key_ingredients"), ";")}
            p = Product(
                catalog_version_id=version.id,
                barcode=(r.get("barcode") or "").strip() or None,
                brand=r["brand"].strip(),
                manufacturer=(r.get("manufacturer") or "").strip() or None,
                name=r["name"].strip(),
                category=r["category"].strip(),
                routine_slot=r["routine_slot"].strip(),
                intended_use=(r.get("intended_use") or "").strip() or None,
                usage_instructions=(r.get("usage_instructions") or "").strip() or None,
                targets=_split(r.get("targets"), ";"),
                suitable_skin_types=_split(r.get("suitable_skin_types"), ";"),
                warnings=_split(r.get("warnings"), ";"),
                price=float(r["price"]) if (r.get("price") or "").strip() else None,
                currency=(r.get("currency") or "").strip() or None,
                price_checked_at=_date(r["price_checked_at"])
                if (r.get("price_checked_at") or "").strip()
                else None,
                available={"true": True, "false": False}.get((r.get("available") or "").strip().lower()),
                availability_note=(r.get("availability_note") or "").strip() or None,
                discovery_url=(r.get("discovery_url") or "").strip() or None,
                source_url=r["source_url"].strip(),
                source_type=r["source_type"].strip(),
                accessed_at=_date(r["accessed_at"]),
                verified_at=_date(r["verified_at"]),
                verification_status="verified",
            )
            for pos, name in enumerate(
                dict.fromkeys(i.upper() for i in _split(r["inci_full"], ";")), start=1
            ):
                ing = ingredients.get(name)
                if ing is None:
                    ing = ingredients[name] = Ingredient(inci_name=name)
                    db.add(ing)
                p.ingredients.append(ProductIngredient(ingredient=ing, position=pos, is_key=name in key))
            db.add(p)
            rep.imported += 1
    if freeze:
        version.frozen = True
    db.commit()
    return rep


def current_version(db: Session) -> CatalogVersion | None:
    """Latest frozen version; falls back to the latest unfrozen one during development."""
    frozen = db.scalar(select(CatalogVersion).where(CatalogVersion.frozen).order_by(CatalogVersion.id.desc()))
    return frozen or db.scalar(select(CatalogVersion).order_by(CatalogVersion.id.desc()))


def load_catalog(db: Session, version_id: int) -> list[ProductIn]:
    out = []
    for p in db.scalars(select(Product).where(Product.catalog_version_id == version_id)):
        ings = sorted(p.ingredients, key=lambda x: x.position)
        out.append(
            ProductIn(
                id=str(p.id),
                brand=p.brand,
                manufacturer=p.manufacturer,
                name=p.name,
                category=p.category,
                routine_slot=p.routine_slot,
                inci=[i.ingredient.inci_name for i in ings],
                key_ingredients=[i.ingredient.inci_name for i in ings if i.is_key],
                targets=p.targets or [],
                warnings=p.warnings or [],
                suitable_skin_types=p.suitable_skin_types or [],
                price=float(p.price) if p.price is not None else None,
                currency=p.currency,
                available=p.available,
                usage_instructions=p.usage_instructions,
                source_url=p.source_url,
                verification_status=p.verification_status,
            )
        )
    return sorted(out, key=lambda x: x.id)
