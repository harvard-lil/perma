"""Unit tests for the pixel comparator; synthetic images, no browser or database."""

import pytest
from PIL import Image

from functional_tests.image_diff import compare_images

TOLERANCE = 3
GREY = (100, 100, 100)


def _solid(size=(10, 10), color=GREY):
    return Image.new("RGB", size, color)


def _with_pixel(image, xy, color):
    image = image.copy()
    image.putpixel(xy, color)
    return image


def _with_block(left):
    image = _solid(color=(255, 255, 255))
    for x in range(left, left + 4):
        for y in range(2, 8):
            image.putpixel((x, y), (0, 0, 0))
    return image


def test_identical_images_pass():
    result = compare_images(_solid(), _solid(), TOLERANCE)

    assert result.passed
    assert result.sizes_match
    assert result.differing_pixels == 0
    assert result.max_channel_difference == 0
    assert result.bbox is None


def test_difference_of_exactly_the_tolerance_passes():
    actual = _with_pixel(_solid(), (4, 5), (GREY[0] + TOLERANCE, GREY[1], GREY[2]))

    result = compare_images(_solid(), actual, TOLERANCE)

    assert result.passed
    assert result.differing_pixels == 0
    assert result.max_channel_difference == TOLERANCE
    assert result.bbox is None


def test_one_channel_one_step_over_the_tolerance_fails_with_that_pixel_highlighted():
    actual = _with_pixel(_solid(), (4, 5), (GREY[0], GREY[1] - TOLERANCE - 1, GREY[2]))

    result = compare_images(_solid(), actual, TOLERANCE)

    assert not result.passed
    assert result.sizes_match
    assert result.differing_pixels == 1
    assert result.max_channel_difference == TOLERANCE + 1
    assert result.bbox == (4, 5, 5, 6)
    assert result.diff_image.size == (10, 10)
    assert result.diff_image.getpixel((4, 5)) == (255, 0, 0)
    assert result.diff_image.getpixel((3, 5)) != (255, 0, 0)


def test_one_pixel_horizontal_shift_of_a_solid_shape_fails():
    result = compare_images(_with_block(3), _with_block(4), TOLERANCE)

    assert not result.passed
    # The shape is 4 x 6; a 1 px shift changes one column on each side.
    assert result.differing_pixels == 2 * 6
    assert result.max_channel_difference == 255
    assert result.bbox == (3, 2, 8, 8)


def test_size_change_fails_and_the_diff_image_is_padded_to_the_larger_size():
    result = compare_images(_solid((10, 10)), _solid((10, 11)), TOLERANCE)

    assert not result.passed
    assert not result.sizes_match
    assert result.baseline_size == (10, 10)
    assert result.actual_size == (10, 11)
    assert result.differing_pixels == 0
    assert result.diff_image.size == (10, 11)
    padded, compared = result.diff_image.getpixel((5, 10)), result.diff_image.getpixel((5, 9))
    assert padded != compared
    assert padded not in {(255, 0, 0), (255, 255, 255)}


def test_size_change_in_both_axes_pads_to_the_larger_width_and_height():
    result = compare_images(_solid((12, 8)), _solid((9, 15)), TOLERANCE)

    assert not result.passed
    assert result.diff_image.size == (12, 15)


def test_worst_difference_and_bounding_box_span_all_differing_pixels():
    actual = _with_pixel(_solid(), (2, 3), (GREY[0] + 10, GREY[1], GREY[2]))
    actual.putpixel((7, 8), (GREY[0], GREY[1], GREY[2] - 40))

    result = compare_images(_solid(), actual, TOLERANCE)

    assert result.differing_pixels == 2
    assert result.max_channel_difference == 40
    assert result.bbox == (2, 3, 8, 9)


def test_images_are_compared_as_rgb():
    result = compare_images(_solid().convert("RGBA"), _solid().convert("L").convert("RGB"), TOLERANCE)

    assert result.passed


@pytest.mark.parametrize("tolerance", [-1, 256])
def test_tolerance_outside_0_to_255_is_rejected(tolerance):
    with pytest.raises(ValueError):
        compare_images(_solid(), _solid(), tolerance)
