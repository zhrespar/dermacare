"""Import a curated catalog CSV (database/seed/product_template.csv columns).

Usage (from backend/, PYTHONPATH=$PWD:$PWD/..):
    python -m app.cli.import_catalog path/to/verified.csv --version 2026.12-v1 [--freeze]

Rejected rows are listed with reasons and NOT imported.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.catalog import import_csv


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--version", required=True, help="catalog version label, e.g. 2026.12-v1")
    ap.add_argument("--freeze", action="store_true", help="freeze the version after import")
    a = ap.parse_args(argv)
    with SessionLocal() as db:
        rep = import_csv(db, a.csv, a.version, a.freeze)
    print(f"imported: {rep.imported}  rejected: {len(rep.rejected)}")
    for line, name, errs in rep.rejected:
        print(f"  line {line} {name!r}: {', '.join(errs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
