import pytest

from ml.inference.interfaces import (
    AcneDetector,
    BoundingBox,
    ImageInput,
    UnderEyeClassifier,
    WrinkleSegmenter,
)
from ml.inference.mock_models import (
    MockAcneDetector,
    MockUnderEyeClassifier,
    MockWrinkleSegmenter,
)


def test_mocks_satisfy_protocols():
    assert isinstance(MockAcneDetector(), AcneDetector)
    assert isinstance(MockWrinkleSegmenter(), WrinkleSegmenter)
    assert isinstance(MockUnderEyeClassifier(), UnderEyeClassifier)


def test_mock_outputs_are_labeled():
    img = ImageInput(image_bytes=b"synthetic", width=1, height=1)
    assert MockAcneDetector().predict(img).model_version == "mock-0"


def test_bbox_validation():
    with pytest.raises(ValueError):
        BoundingBox(0.5, 0.5, 0.4, 0.6, 0.9)
