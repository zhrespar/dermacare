"""Framework-free evaluation metrics (pure Python) so they can be unit-tested without torch.

Detection mAP uses the standard all-point interpolated AP at a single IoU threshold.
"""

from __future__ import annotations

Box = tuple[float, float, float, float]


def iou(a: Box, b: Box) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def dice_iou_binary(pred: list[int], target: list[int]) -> tuple[float, float]:
    """Flattened binary masks. Both empty -> (1, 1)."""
    tp = sum(1 for p, t in zip(pred, target, strict=True) if p and t)
    fp = sum(1 for p, t in zip(pred, target, strict=True) if p and not t)
    fn = sum(1 for p, t in zip(pred, target, strict=True) if t and not p)
    if tp + fp + fn == 0:
        return 1.0, 1.0
    return 2 * tp / (2 * tp + fp + fn), tp / (tp + fp + fn)


def confusion(y_true: list[int], y_pred: list[int], n: int) -> list[list[int]]:
    m = [[0] * n for _ in range(n)]
    for t, p in zip(y_true, y_pred, strict=True):
        m[t][p] += 1
    return m


def macro_f1(y_true: list[int], y_pred: list[int], n: int) -> float:
    m = confusion(y_true, y_pred, n)
    f1s = []
    for c in range(n):
        tp = m[c][c]
        fp = sum(m[r][c] for r in range(n)) - tp
        fn = sum(m[c]) - tp
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(f1s) / n


def quadratic_weighted_kappa(y_true: list[int], y_pred: list[int], n: int) -> float:
    o = confusion(y_true, y_pred, n)
    total = len(y_true)
    ht = [sum(o[i]) for i in range(n)]
    hp = [sum(o[i][j] for i in range(n)) for j in range(n)]
    num = den = 0.0
    for i in range(n):
        for j in range(n):
            w = (i - j) ** 2 / (n - 1) ** 2
            num += w * o[i][j]
            den += w * ht[i] * hp[j] / total
    return 1.0 - num / den if den else 1.0


def binary_f1(y_true: list[int], y_pred: list[int]) -> float:
    tp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if p and not t)
    fn = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t and not p)
    return 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)


def roc_auc(y_true: list[int], scores: list[float]) -> float:
    """Mann-Whitney formulation, ties count 0.5."""
    pos = [s for s, t in zip(scores, y_true, strict=True) if t]
    neg = [s for s, t in zip(scores, y_true, strict=True) if not t]
    if not pos or not neg:
        raise ValueError("need both classes")
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def average_precision(
    preds: list[tuple[str, float, Box]], gts: dict[str, list[Box]], iou_thr: float = 0.5
) -> float:
    """preds: (image_id, confidence, box). gts: image_id -> boxes. Single class."""
    n_gt = sum(len(v) for v in gts.values())
    if n_gt == 0:
        return 0.0
    used = {k: [False] * len(v) for k, v in gts.items()}
    tps: list[int] = []
    for img, _, box in sorted(preds, key=lambda p: -p[1]):
        best, bi = 0.0, -1
        for i, g in enumerate(gts.get(img, [])):
            v = iou(box, g)
            if v > best:
                best, bi = v, i
        if best >= iou_thr and not used[img][bi]:
            used[img][bi] = True
            tps.append(1)
        else:
            tps.append(0)
    prec, rec, tp = [], [], 0
    for k, t in enumerate(tps, 1):
        tp += t
        prec.append(tp / k)
        rec.append(tp / n_gt)
    for i in range(len(prec) - 2, -1, -1):  # monotone precision envelope
        prec[i] = max(prec[i], prec[i + 1])
    ap, prev_r = 0.0, 0.0
    for p, r in zip(prec, rec, strict=True):
        ap += p * (r - prev_r)
        prev_r = r
    return ap
