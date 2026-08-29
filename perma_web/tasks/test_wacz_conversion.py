from datetime import datetime, timedelta, timezone

import pytest

from tasks.wacz_conversion import get_conversion_queryset


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("option", "cutoff"),
    [
        ("legacy_warcs", datetime(2014, 5, 1, tzinfo=timezone.utc)),
        ("old_style_guids", datetime(2013, 11, 22, tzinfo=timezone.utc)),
    ],
)
def test_conversion_queryset_selects_only_links_before_legacy_cutoff(
    link_factory, option, cutoff
):
    before_cutoff = link_factory(
        creation_timestamp=cutoff - timedelta(microseconds=1),
        cached_can_play_back=True,
    )
    link_factory(creation_timestamp=cutoff, cached_can_play_back=True)

    guids = get_conversion_queryset(
        source_csv=None,
        guid=None,
        big_warcs=False,
        legacy_warcs=option == "legacy_warcs",
        old_style_guids=option == "old_style_guids",
        user_uploads=False,
        batch_guid_prefix=None,
        batch_range=None,
        batch_size=None,
    )

    assert list(guids) == [before_cutoff.guid]
