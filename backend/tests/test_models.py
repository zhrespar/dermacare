import app.models  # noqa: F401
from app.db.base import Base
from sqlalchemy import create_engine, inspect


def test_metadata_creates_all_tables():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    tables = set(inspect(eng).get_table_names())
    assert {
        "users",
        "skin_profiles",
        "face_images",
        "analyses",
        "catalog_versions",
        "ingredients",
        "products",
        "product_ingredients",
        "recommendations",
        "recommendation_items",
    } <= tables
