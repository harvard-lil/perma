"""
Pixel comparison of two images, for visual-regression tests.

Deals in images only: no Playwright, no pytest. All pixel work is done by
Pillow's C routines, since full-page screenshots reach about 1200 x 8800 px.
"""

from dataclasses import dataclass

from PIL import Image, ImageChops

_DIFF_COLOR = (255, 0, 0)
_PADDING_COLOR = (0, 120, 255)
_FADE_TOWARD_WHITE = 0.3  # share of the actual image kept in the diff image

# Per channel, out of 255; must stay above the 1-2/255 colour rounding seen between arm64 and amd64 renders.
# Defined here, not in conftest, so the review report can use the suite's tolerance without importing Django.
SNAPSHOT_TOLERANCE = 3


@dataclass(frozen=True)
class ImageComparison:
    """
    The outcome of `compare_images`.

    `differing_pixels`, `max_channel_difference` and `bbox` describe only the
    area both images cover. Where sizes differ, the extra rows or columns are
    not counted; `sizes_match` is False and the comparison fails.

    `bbox` is (left, upper, right, lower) of the differing pixels, or None.
    `diff_image` is as large as the bigger image on each axis: a faded copy of
    the actual image, differing pixels in red, and everything outside the area
    both images cover in solid blue.
    """

    baseline_size: tuple[int, int]
    actual_size: tuple[int, int]
    differing_pixels: int
    max_channel_difference: int
    bbox: tuple[int, int, int, int] | None
    diff_image: Image.Image

    @property
    def sizes_match(self) -> bool:
        return self.baseline_size == self.actual_size

    @property
    def passed(self) -> bool:
        return self.sizes_match and self.differing_pixels == 0


def compare_images(baseline: Image.Image, actual: Image.Image, tolerance: int) -> ImageComparison:
    """
    Compare two images pixel by pixel.

    A pixel differs when any RGB channel is off by more than `tolerance`
    (0-255); a difference of exactly `tolerance` passes. Both images are
    converted to RGB first, so transparency is ignored.

    Args:
        baseline: The expected image.
        actual: The image under test.
        tolerance: Largest per-channel difference, out of 255, that still counts as equal.

    Returns:
        An `ImageComparison`. Different sizes always give a result that did not pass.

    Raises:
        ValueError: If `tolerance` is outside 0-255.
    """
    if not 0 <= tolerance <= 255:
        raise ValueError(f"tolerance must be between 0 and 255, got {tolerance}")

    baseline = baseline.convert("RGB")
    actual = actual.convert("RGB")
    overlap = (min(baseline.width, actual.width), min(baseline.height, actual.height))
    union = (max(baseline.width, actual.width), max(baseline.height, actual.height))

    difference = ImageChops.difference(baseline.crop((0, 0, *overlap)), actual.crop((0, 0, *overlap)))
    over_tolerance = [255 if value > tolerance else 0 for value in range(256)]
    red, green, blue = (band.point(over_tolerance) for band in difference.split())
    differing = ImageChops.lighter(ImageChops.lighter(red, green), blue)

    return ImageComparison(
        baseline_size=baseline.size,
        actual_size=actual.size,
        differing_pixels=differing.histogram()[255],
        max_channel_difference=max(high for _, high in difference.getextrema()),
        bbox=differing.getbbox(),
        diff_image=_draw_diff(actual, union, differing),
    )


def _draw_diff(actual: Image.Image, union: tuple[int, int], differing: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", union, _PADDING_COLOR)
    shared = actual.crop((0, 0, *differing.size))
    canvas.paste(Image.blend(Image.new("RGB", shared.size, "white"), shared, _FADE_TOWARD_WHITE), (0, 0))
    canvas.paste(Image.new("RGB", differing.size, _DIFF_COLOR), (0, 0), differing)
    return canvas
