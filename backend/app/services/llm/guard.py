"""Post-generation checks: groundedness (citations) and safety (scope/medical wording).

If a response fails, the explanation service discards it and returns the rule-based text.
The term list is a conservative engineering filter, not a clinical safety evaluation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CITATION_RE = re.compile(r"\[(S\d+)\]")
_SENT_RE = re.compile(r"(?<=[.!?])\s+")

# Diagnostic / treatment wording the prototype must never produce (EN + TR stems).
FORBIDDEN_PATTERNS = [
    r"\bdiagnos",
    r"\bteşhis",
    r"\btanı\b",
    r"\bprescri",
    r"\breçete",
    r"\bcure[sd]?\b",
    r"\btedavi",
    r"\bisotretinoin",
    r"\bantibiotic",
    r"\bantibiyotik",
    r"\brosacea\b",
    r"\bmelanoma\b",
    r"\bdermatitis\b",
]


@dataclass
class GuardReport:
    grounded_ratio: float
    invalid_citations: list[str] = field(default_factory=list)
    unknown_products: list[str] = field(default_factory=list)
    flagged_terms: list[str] = field(default_factory=list)

    @property
    def safe(self) -> bool:
        return not self.flagged_terms

    def passes(self, min_grounded: float = 0.6) -> bool:
        return (
            self.safe
            and not self.invalid_citations
            and not self.unknown_products
            and self.grounded_ratio >= min_grounded
        )


def check_output(
    text: str, source_ids: set[str], product_ids: set[str], mentioned_ids: set[str]
) -> GuardReport:
    """`mentioned_ids` = product ids the text references via {P:...} markers."""
    sentences = [s for s in _SENT_RE.split(text.strip()) if s.strip()]
    cited = [s for s in sentences if CITATION_RE.search(s)]
    all_cites = set(CITATION_RE.findall(text))
    flagged = sorted({m.group(0).lower() for p in FORBIDDEN_PATTERNS for m in re.finditer(p, text, re.I)})
    return GuardReport(
        grounded_ratio=round(len(cited) / len(sentences), 3) if sentences else 0.0,
        invalid_citations=sorted(all_cites - source_ids),
        unknown_products=sorted(mentioned_ids - product_ids),
        flagged_terms=flagged,
    )
