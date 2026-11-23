from fastapi import APIRouter

from app.core.config import get_settings
from app.services.recommendation import RULES_VERSION

router = APIRouter(prefix="/system", tags=["system"])

# Which parts are trained by the project, which reuse pretrained models, which are rules, which call APIs.
COMPONENTS = [
    {"component": "acne_detection_severity", "kind": "trained_by_project", "method": "transfer learning"},
    {"component": "wrinkle_segmentation", "kind": "trained_by_project", "method": "transfer learning"},
    {"component": "under_eye_classification", "kind": "trained_by_project", "method": "transfer learning"},
    {"component": "face_landmarks_regions", "kind": "pretrained", "method": "landmark model + geometry"},
    {"component": "quality_check", "kind": "rule_based", "method": "OpenCV metrics + thresholds"},
    {"component": "triage", "kind": "rule_based", "method": "confidence/scope thresholds"},
    {"component": "recommendation_engine", "kind": "rule_based", "method": "hard filters + weighted score"},
    {"component": "rag_embeddings", "kind": "pretrained", "method": "sentence embedding model"},
    {"component": "rag_retrieval", "kind": "rule_based", "method": "pgvector cosine search"},
    {"component": "explanation_llm", "kind": "external_api", "method": "Anthropic / OpenAI / Gemini"},
]


@router.get("/components")
def components() -> dict:
    s = get_settings()
    return {
        "components": COMPONENTS,
        "active": {
            "analysis_backend": s.analysis_backend,
            "llm_provider": s.llm_provider,
            "llm_model": s.llm_model,
            "rag_store": s.rag_store,
            "rag_embedding_backend": s.rag_embedding_backend,
            "rules_version": RULES_VERSION,
        },
    }
