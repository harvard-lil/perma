import os
from pathlib import Path

import pytest

from perma.models import Sponsorship
from perma.utils import imagemagick_temp_dir, temporary_working_directory


def test_temporary_working_directory_restores_directory_and_removes_it(tmp_path):
    original_directory = Path.cwd()

    with temporary_working_directory() as directory:
        temporary_path = Path(directory)
        assert temporary_path.is_dir()
        assert Path.cwd() == temporary_path

    assert Path.cwd() == original_directory
    assert not temporary_path.exists()


def test_temporary_working_directory_restores_directory_after_an_error():
    original_directory = Path.cwd()

    with pytest.raises(RuntimeError):
        with temporary_working_directory() as directory:
            temporary_path = Path(directory)
            raise RuntimeError("test error")

    assert Path.cwd() == original_directory
    assert not temporary_path.exists()


def test_imagemagick_temp_dir_restores_environment_and_removes_directory(monkeypatch):
    monkeypatch.setenv("MAGICK_TEMPORARY_PATH", "original-path")

    with imagemagick_temp_dir():
        temporary_path = Path(os.environ["MAGICK_TEMPORARY_PATH"])
        assert temporary_path.is_dir()

    assert os.environ["MAGICK_TEMPORARY_PATH"] == "original-path"
    assert not temporary_path.exists()


def test_imagemagick_temp_dir_restores_environment_after_an_error(monkeypatch):
    monkeypatch.delenv("MAGICK_TEMPORARY_PATH", raising=False)

    with pytest.raises(RuntimeError):
        with imagemagick_temp_dir():
            temporary_path = Path(os.environ["MAGICK_TEMPORARY_PATH"])
            raise RuntimeError("test error")

    assert "MAGICK_TEMPORARY_PATH" not in os.environ
    assert not temporary_path.exists()


@pytest.mark.parametrize(
    "fixture_name",
    [
        "registrar_factory",
        "pending_registrar_factory",
        "denied_registrar_factory",
        "nonpaying_registrar_factory",
        "paying_registrar_factory",
        "organization_factory",
        "link_user_factory",
        "deactivated_user_factory",
        "unactivated_user_factory",
        "registrar_user_factory",
        "pending_registrar_user_factory",
        "paying_registrar_user_factory",
        "sponsorship_factory",
        "sponsored_user_factory",
        "nonpaying_user_factory",
        "paying_user_factory",
        "capture_job_factory",
        "invalid_capture_job_factory",
        "pending_capture_job_factory",
        "in_progress_capture_job_factory",
        "completed_capture_job_factory",
        "link_factory",
        "capture_factory",
        "primary_capture_factory",
        "screenshot_capture_factory",
        "folder_factory",
        "sponsored_folder_factory",
    ],
)
def test_factory_fixture_names_remain_available(request, fixture_name):
    assert request.getfixturevalue(fixture_name).__name__.endswith("Factory")


def test_post_generation_factories_persist_their_related_records(
    registrar_factory,
    sponsored_user_factory,
):
    registrar = registrar_factory()
    sponsored_user = sponsored_user_factory()

    assert registrar.organizations.count() == 1
    assert Sponsorship.objects.filter(user=sponsored_user).count() == 1


@pytest.mark.parametrize(
    ("submitted_url", "expected_surt"),
    [
        ("http://example.com/", "com,example)/"),
        ("https://www.example.com/path?x=1", "com,example)/path?x=1"),
        ("https://example.com:8443/a%20path", "com,example:8443)/a%20path"),
    ],
)
def test_link_factory_persists_canonical_surt(link_factory, submitted_url, expected_surt):
    link = link_factory(submitted_url=submitted_url)

    assert link.submitted_url_surt == expected_surt
