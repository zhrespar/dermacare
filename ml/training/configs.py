"""Transfer-learning experiment configs for the three CV tasks (the only components we train).

Architectures are CANDIDATES to compare on the validation split, all starting from public
pretrained weights. Nothing here has been trained; no results exist. Hyperparameters are
starting points, recorded so every run is reproducible (see docs/ML_EXPERIMENTS.md).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    license: str
    drive_path: str  # Drive 02_Datasets/... — mounted in Colab only after licence is confirmed
    labels: str
    commercial_use: bool


@dataclass(frozen=True)
class TrainConfig:
    task: str
    dataset: DatasetSpec
    candidates: tuple[str, ...]  # pretrained backbones/architectures to compare
    pretrained_on: str
    input_size: int
    epochs: int
    batch_size: int
    lr: float
    freeze_backbone_epochs: int  # warm-up with frozen backbone, then fine-tune all layers
    primary_metric: str
    seed: int = 42
    augmentations: tuple[str, ...] = ("hflip", "color_jitter_light", "random_resized_crop")
    notes: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


ACNE04 = DatasetSpec(
    name="ACNE04",
    license="Research use — confirm terms with dataset authors before use (LICENSE_NOTES)",
    drive_path="02_Datasets/ACNE04",
    labels="lesion bounding boxes + 4-level image severity (Hayashi)",
    commercial_use=False,
)
FFHQ_WRINKLE = DatasetSpec(
    name="FFHQ-Wrinkle",
    license="CC BY-NC-SA 4.0",
    drive_path="02_Datasets/FFHQ-Wrinkle",
    labels="50k weak masks (pre-training) + 1,000 manual masks (fine-tune/eval)",
    commercial_use=False,
)
CELEBA = DatasetSpec(
    name="CelebA",
    license="Non-commercial research",
    drive_path="02_Datasets/CelebA",
    labels="Bags_Under_Eyes binary attribute (periocular crop)",
    commercial_use=False,
)

ACNE_DETECTION = TrainConfig(
    task="acne_detection",
    dataset=ACNE04,
    candidates=("yolov8s", "faster_rcnn_resnet50_fpn"),
    pretrained_on="COCO",
    input_size=640,
    epochs=100,
    batch_size=16,
    lr=1e-3,
    freeze_backbone_epochs=5,
    primary_metric="mAP@0.5",
    augmentations=("hflip", "color_jitter_light", "mosaic"),
)
ACNE_SEVERITY = TrainConfig(
    task="acne_severity",
    dataset=ACNE04,
    candidates=("efficientnet_b0", "resnet50", "convnext_tiny"),
    pretrained_on="ImageNet-1k",
    input_size=384,
    epochs=40,
    batch_size=32,
    lr=3e-4,
    freeze_backbone_epochs=3,
    primary_metric="macro_f1",
    notes="class-balanced loss or sampling; report confusion matrix + quadratic weighted kappa",
)
WRINKLE_SEGMENTATION = TrainConfig(
    task="wrinkle_segmentation",
    dataset=FFHQ_WRINKLE,
    candidates=("unet_resnet34", "unet_efficientnet_b3"),
    pretrained_on="ImageNet-1k (encoder)",
    input_size=512,
    epochs=60,
    batch_size=8,
    lr=3e-4,
    freeze_backbone_epochs=0,
    primary_metric="dice",
    notes="stage 1: weak masks; stage 2: fine-tune on manual masks; Dice+BCE loss for thin structures",
)
UNDER_EYE = TrainConfig(
    task="under_eye_classification",
    dataset=CELEBA,
    candidates=("efficientnet_b0", "resnet50"),
    pretrained_on="ImageNet-1k",
    input_size=224,
    epochs=20,
    batch_size=64,
    lr=3e-4,
    freeze_backbone_epochs=2,
    primary_metric="f1",
    notes="threshold chosen on validation; Grad-CAM for visual explanation",
)

ALL_CONFIGS = {c.task: c for c in (ACNE_DETECTION, ACNE_SEVERITY, WRINKLE_SEGMENTATION, UNDER_EYE)}
