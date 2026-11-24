"""Step 1 of the portrait: clean up your photo so it converts well to ASCII.

Usage (from the repo folder):
    python scripts/prep_photo.py source-photo.jpg

Output: source-prepped.png (grayscale, background removed, white backdrop)

Note: some Windows PCs block certain compiled library files ("Application Control").
This script avoids OpenCV, and if the rembg library cannot load it automatically falls
back to a simple background remover that works well with a plain-colour backdrop.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from skimage import exposure

ROOT = Path(__file__).resolve().parent.parent


def remove_plain_background(img):
    """Pure PIL + numpy background remover for photos with a plain, even backdrop.
    Returns (rgb uint8 array, alpha float array 0..1)."""
    rgb = np.asarray(img.convert("RGB"))
    H, W, _ = rgb.shape
    f = rgb.astype(np.float32)

    # Estimate the backdrop colour from the top strip and the upper sides of the photo.
    samples = np.concatenate([
        f[: max(4, H // 20), :, :].reshape(-1, 3),
        f[: int(H * 0.35), : max(4, W // 30), :].reshape(-1, 3),
        f[: int(H * 0.35), -max(4, W // 30) :, :].reshape(-1, 3),
    ])
    bg = np.median(samples, axis=0)
    dist = np.sqrt(((f - bg) ** 2).sum(axis=2))

    # 255 = "looks like backdrop", then keep only the backdrop region connected to the top edge.
    similar = Image.fromarray(np.where(dist < 38, 255, 0).astype(np.uint8), "L")
    similar = similar.filter(ImageFilter.MedianFilter(5))
    for seed in [(2, 2), (W - 3, 2), (W // 2, 2), (2, H // 4), (W - 3, H // 4)]:
        if similar.getpixel(seed) == 255:
            ImageDraw.floodfill(similar, seed, 128, thresh=0)
    is_bg = np.asarray(similar) == 128

    alpha = Image.fromarray(np.where(is_bg, 0, 255).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.GaussianBlur(1.5))
    return rgb, np.asarray(alpha).astype(np.float32) / 255.0


def build(rgb, alpha):
    """rgb: HxWx3 uint8, alpha: HxW float 0..1 (1 = person). Returns a grayscale uint8 image."""
    ys, xs = np.where(alpha > 0.5)
    if len(xs) == 0:
        raise SystemExit("No person found in the photo.")
    H, W = alpha.shape
    top, bottom = ys.min(), ys.max()
    sub_h = bottom - top

    # Find the head: the widest part of the top third of the person.
    head_rows = alpha[top : top + int(sub_h * 0.30)] > 0.5
    hx = np.where(head_rows.any(axis=0))[0]
    cx, head_w = int((hx.min() + hx.max()) / 2), int(hx.max() - hx.min())

    # Crop to head + upper shoulders so the face fills the ASCII grid.
    crop_w = int(head_w * 2.3)
    crop_h = int(crop_w * 1.0)
    pad_top = int(head_w * 0.10)
    x0, x1 = max(cx - crop_w // 2, 0), min(cx + crop_w // 2, W)
    y0, y1 = max(top - pad_top, 0), min(top - pad_top + crop_h, H)
    rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    # Grayscale (standard luminance weights).
    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).astype(np.float32)

    # Stretch contrast using only the person's pixels, then lift mid-tones a little
    # so darker skin tones keep visible features.
    person = gray[alpha > 0.5]
    lo, hi = np.percentile(person, 2), np.percentile(person, 98)
    gray = ((gray - lo) / max(hi - lo, 1)).clip(0, 1) ** 0.75

    # Local contrast (CLAHE): gives a flatly lit face real highlights and shadows.
    kernel = max(16, min(gray.shape) // 8)
    gray = exposure.equalize_adapthist(gray, kernel_size=kernel, clip_limit=0.03)
    gray = (gray * 255).astype(np.float32)

    # Composite onto pure white so the background becomes blank space.
    out = gray * alpha + 255.0 * (1.0 - alpha)
    return out.clip(0, 255).astype(np.uint8)


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source-photo.jpg")
    if not src.exists() and (ROOT / src).exists():
        src = ROOT / src
    if not src.exists():
        sys.exit(f"Could not find the photo: {src}")
    photo = Image.open(src).convert("RGB")

    try:
        from rembg import remove  # best quality, works on any background

        print("Removing background with rembg... (the first run downloads a model, please wait)")
        cut = np.array(remove(photo).convert("RGBA"))
        rgb, alpha = cut[:, :, :3], cut[:, :, 3].astype(np.float32) / 255.0
    except Exception as err:  # e.g. DLL blocked by Windows Application Control
        print(f"rembg could not run ({type(err).__name__}); using the simple background remover instead.")
        print("This works best when the photo has a plain, even background.")
        rgb, alpha = remove_plain_background(photo)

    out = build(rgb, alpha)
    Image.fromarray(out, "L").save(ROOT / "source-prepped.png")
    print("Saved source-prepped.png")
