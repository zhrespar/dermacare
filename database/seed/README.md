# Seed data

**No product records are committed yet.** The verified catalog (>=100 products) is built per
`docs/DATABASE_SCHEMA.md` (Catalog verification workflow): candidates from Open Beauty Facts (ODbL),
INCI lists cross-checked against the manufacturer's official page/packaging, INCI names normalised with
CosIng. Only `verification_status = verified` products enter the recommendation pool.

- `product_template.csv`: column template for catalog curation (header only).
- Verified rows are prepared in Drive `05_Product_Data/Verified_Catalog/` and imported by a seed
  script once a catalog version is frozen.
- `knowledge_template.csv`: column template for the RAG knowledge base (header only). Each row is a
  vetted source (scientific article, dermatology guideline, CosIng/ingredient entry, manufacturer
  page) whose licence permits storing excerpts. Only `verified` rows are ingested
  (`Retriever.ingest` rejects anything else). No knowledge documents are committed yet.

`discovery_url` (e.g. Open Beauty Facts) records where a candidate was found; `source_url` must be the
authoritative source (manufacturer page or package) used to verify the INCI list.
