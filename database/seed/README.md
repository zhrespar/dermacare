# Seed data

**No product records are committed yet.** The verified catalog (>=100 products) is built per
`docs/DATABASE_SCHEMA.md` (Catalog verification workflow): candidates from Open Beauty Facts (ODbL),
INCI lists cross-checked against the manufacturer's official page/packaging, INCI names normalised with
CosIng. Only `verification_status = verified` products enter the recommendation pool.

- `product_template.csv`: column template for catalog curation (header only).
- Verified rows are prepared in Drive `05_Product_Data/Verified_Catalog/` and imported by a seed
  script once a catalog version is frozen.
