"""
Image preprocessing pipeline for OCR accuracy improvement.

Applies grayscale conversion, denoising, adaptive thresholding, deskewing,
and resizing before the image is handed off to the OCR engine. OCR engines
are trained on relatively clean text; scanned or phone-photographed
documents rarely are, so this pipeline exists to close that gap before the
image ever reaches EasyOCR/Tesseract.
"""

from __future__ import annotations

import cv2
import numpy as np

import config
from src.utils import get_logger

logger = get_logger(__name__)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert an RGB/BGR image to single-channel grayscale.

    Color carries no information for text recognition and only slows down
    every downstream step, so it's dropped as early as possible.
    """
    if image.ndim == 2:
        # Already single-channel (e.g. a re-processed image) — nothing to do.
        return image
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def denoise(image: np.ndarray) -> np.ndarray:
    """Remove speckle noise while preserving text edges.

    fastNlMeansDenoising compares small patches across the whole image
    rather than just blurring neighboring pixels, so it smooths out
    scanner/camera sensor noise without also smearing character edges —
    which a simple Gaussian blur would do and which actively hurts OCR.
    """
    return cv2.fastNlMeansDenoising(image, h=config.DENOISE_STRENGTH)


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Binarize the image using adaptive Gaussian thresholding.

    Adaptive thresholding handles uneven lighting/scan shadows far better
    than a single global threshold, which matters for phone-camera captures.
    Each pixel's threshold is computed from a Gaussian-weighted average of
    its local neighborhood (ADAPTIVE_THRESH_BLOCK_SIZE), so a shadow on one
    side of the page doesn't wash out text on that side while leaving the
    rest untouched.
    """
    return cv2.adaptiveThreshold(
        image,
        255,  # value assigned to pixels above their local threshold (pure white)
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.ADAPTIVE_THRESH_BLOCK_SIZE,  # size of the neighborhood used per pixel
        config.ADAPTIVE_THRESH_C,  # constant subtracted from the local mean
    )


def deskew(image: np.ndarray) -> np.ndarray:
    """Detect and correct small rotational skew using the minimum-area bounding box.

    Scanned/photographed documents are rarely perfectly aligned; even a
    2-3 degree tilt measurably degrades OCR word accuracy.
    """
    # Collect the (row, col) coordinates of every "dark" pixel (i.e. ink/text
    # against a lighter background). These are the points the bounding box
    # below is fit around.
    coords = np.column_stack(np.where(image < 255))
    if coords.size == 0:
        # A blank image has nothing to align to.
        return image

    # minAreaRect finds the smallest rotated rectangle enclosing all the dark
    # pixels; its angle tells us how far the block of text is tilted.
    angle = cv2.minAreaRect(coords)[-1]

    # OpenCV reports the rectangle's angle in the range (-90, 0], which maps
    # ambiguously onto "how far is the text rotated from horizontal". This
    # normalizes it into an intuitive rotation-to-correct value.
    angle = -(90 + angle) if angle < -45 else -angle

    if abs(angle) < 0.1:
        # Sub-0.1-degree "skew" is just measurement noise on an already
        # straight page — rotating would add blur for zero benefit.
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image, matrix, (w, h),
        flags=cv2.INTER_CUBIC,  # smooth interpolation to avoid jagged rotated edges
        borderMode=cv2.BORDER_REPLICATE,  # extend edge pixels instead of introducing black corners
    )


def resize_if_needed(image: np.ndarray) -> np.ndarray:
    """Downscale images whose longest side exceeds RESIZE_MAX_DIMENSION.

    Keeps OCR runtime bounded for very high-resolution scans without
    materially hurting accuracy — OCR engines have their own internal
    minimum useful resolution, so pixels beyond that just cost time.
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= config.RESIZE_MAX_DIMENSION:
        return image

    scale = config.RESIZE_MAX_DIMENSION / longest
    new_size = (int(w * scale), int(h * scale))
    # INTER_AREA gives the best quality when shrinking an image (as opposed
    # to INTER_CUBIC/LINEAR, which are better suited to enlarging).
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Run the full preprocessing pipeline and return an OCR-ready image.

    Order matters:
      1. Resize first — every later step is O(pixels), so shrinking early
         makes the rest of the pipeline cheaper.
      2. Grayscale — collapses 3 channels to 1 before any per-pixel work.
      3. Denoise — clean up sensor/scan noise before it can distort the
         skew-angle estimate or the threshold boundary.
      4. Deskew — straighten the page while it's still grayscale (rotating
         a binary image would introduce jagged, half-gray edge artifacts).
      5. Threshold — binarize last, once the image is clean and level, so
         the black/white boundary falls exactly on the text edges.
    """
    logger.info("Starting image preprocessing pipeline")

    processed = resize_if_needed(image)
    processed = to_grayscale(processed)
    processed = denoise(processed)

    if config.DESKEW_ENABLED:
        processed = deskew(processed)

    processed = adaptive_threshold(processed)

    logger.info("Preprocessing complete: shape=%s", processed.shape)
    return processed
