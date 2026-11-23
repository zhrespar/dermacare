"""Initial relational model. Keep in sync with docs/DATABASE_SCHEMA.md and Alembic."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_version: Mapped[str | None] = mapped_column(String(32))
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profiles: Mapped[list["SkinProfile"]] = relationship(back_populates="user")


class SkinProfile(TimestampMixin, Base):
    """User-declared data. Unknown values stay NULL — never assumed negative."""

    __tablename__ = "skin_profiles"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    skin_type: Mapped[str | None] = mapped_column(String(16))  # dry|oily|combination|normal
    sensitivity: Mapped[str | None] = mapped_column(String(16))  # none|mild|high
    allergies: Mapped[list | None] = mapped_column(JSON)  # INCI names
    avoid_ingredients: Mapped[list | None] = mapped_column(JSON)
    goals: Mapped[list | None] = mapped_column(JSON)
    current_routine: Mapped[dict | None] = mapped_column(JSON)
    past_reactions: Mapped[str | None] = mapped_column(Text)
    past_reaction_ingredients: Mapped[list | None] = mapped_column(JSON)  # INCI; hard-excluded
    budget_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    preferences: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="profiles")


class FaceImage(TimestampMixin, Base):
    """Metadata only. Raw image bytes live in private object storage, referenced by key."""

    __tablename__ = "face_images"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    storage_key: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    quality_status: Mapped[str] = mapped_column(String(16))  # accepted|retake|out_of_scope
    quality_reasons: Mapped[list | None] = mapped_column(JSON)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    face_image_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("face_images.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(16))  # completed|limited|referred|failed
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    acne: Mapped[dict | None] = mapped_column(JSON)
    wrinkles: Mapped[dict | None] = mapped_column(JSON)
    under_eye: Mapped[dict | None] = mapped_column(JSON)
    triage: Mapped[dict | None] = mapped_column(JSON)
    model_versions: Mapped[dict] = mapped_column(JSON)


class CatalogVersion(TimestampMixin, Base):
    __tablename__ = "catalog_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(32), unique=True)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inci_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    cosing_ref: Mapped[str | None] = mapped_column(String(64))
    functions: Mapped[list | None] = mapped_column(JSON)


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = _pk()
    catalog_version_id: Mapped[int] = mapped_column(ForeignKey("catalog_versions.id"))
    barcode: Mapped[str | None] = mapped_column(String(32), index=True)
    brand: Mapped[str] = mapped_column(String(128))
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(32))  # cleanser|serum|moisturizer|sunscreen|eye
    routine_slot: Mapped[str] = mapped_column(String(8))  # am|pm|both
    intended_use: Mapped[str | None] = mapped_column(Text)
    usage_instructions: Mapped[str | None] = mapped_column(Text)  # manufacturer's directions
    targets: Mapped[list | None] = mapped_column(JSON)  # needs, assigned by expert-reviewed rules
    suitable_skin_types: Mapped[list | None] = mapped_column(JSON)
    warnings: Mapped[list | None] = mapped_column(JSON)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    price_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available: Mapped[bool | None] = mapped_column(Boolean)
    availability_note: Mapped[str | None] = mapped_column(String(255))  # e.g. market/retailer
    discovery_url: Mapped[str | None] = mapped_column(String(1024))  # e.g. Open Beauty Facts (discovery only)
    source_url: Mapped[str] = mapped_column(String(1024))
    source_type: Mapped[str] = mapped_column(String(32))  # manufacturer|package (verification source)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[str] = mapped_column(String(16))  # pending|verified|rejected

    ingredients: Mapped[list["ProductIngredient"]] = relationship(cascade="all, delete-orphan")


class ProductIngredient(Base):
    __tablename__ = "product_ingredients"
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer)
    is_key: Mapped[bool] = mapped_column(Boolean, default=False)
    ingredient: Mapped[Ingredient] = relationship()


class Recommendation(TimestampMixin, Base):
    __tablename__ = "recommendations"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("analyses.id", ondelete="SET NULL"))
    catalog_version_id: Mapped[int] = mapped_column(ForeignKey("catalog_versions.id"))
    rules_version: Mapped[str] = mapped_column(String(32))
    mode: Mapped[str] = mapped_column(String(16))  # profile_only|image_only|multimodal
    needs: Mapped[list] = mapped_column(JSON)
    explanation: Mapped[str | None] = mapped_column(Text)
    items: Mapped[list["RecommendationItem"]] = relationship(cascade="all, delete-orphan")


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recommendations.id", ondelete="CASCADE"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    routine_slot: Mapped[str] = mapped_column(String(8))
    step_order: Mapped[int] = mapped_column(Integer)
    total_score: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict] = mapped_column(JSON)
    reasons: Mapped[list] = mapped_column(JSON)
