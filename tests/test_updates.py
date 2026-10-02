from __future__ import annotations

import pytest
import requests

from keyenroll import PROJECT_URL, updates
from keyenroll.updates import UpdateError, UpdateInfo, parse_version


class Response:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body

    def json(self):
        if self._body is None:
            raise ValueError("not JSON")
        return self._body


class Http:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def get(self, url, headers=None, timeout=None):
        self.calls.append((url, headers, timeout))
        if self.error:
            raise self.error
        return self.response


def release(tag, url=None):
    return Response(200, {"tag_name": tag, "html_url": url or f"{PROJECT_URL}/releases/tag/{tag}"})


def test_versions_compare_as_numbers_not_text():
    assert parse_version("v0.10.0") > parse_version("0.9.9")
    assert parse_version("1.0") == parse_version("v1.0.0") == (1,)
    assert parse_version("2.1.0rc1") == (2, 1)
    assert parse_version(" v3.4.5+build7 ") == (3, 4, 5)
    with pytest.raises(ValueError):
        parse_version("latest")


def test_newer_release_is_reported_with_its_page():
    http = Http(release("v0.4.0"))
    info = updates.check(http, current="0.3.0")
    assert info == UpdateInfo("0.3.0", "0.4.0", f"{PROJECT_URL}/releases/tag/v0.4.0")
    assert info.newer
    url, headers, timeout = http.calls[0]
    assert url == "https://api.github.com/repos/inowakowski/KeyEnroll/releases/latest"
    assert headers["User-Agent"] == "KeyEnroll/0.3.0" and timeout


@pytest.mark.parametrize("tag", ["v0.3.0", "0.3", "v0.2.9"])
def test_same_or_older_release_is_not_an_update(tag):
    assert not updates.check(Http(release(tag)), current="0.3.0").newer


def test_running_a_newer_build_than_the_published_one():
    assert not updates.check(Http(release("v0.3.0")), current="0.4.0").newer


def test_private_repository_or_no_release_is_explained():
    with pytest.raises(UpdateError, match="No published release"):
        updates.check(Http(Response(404, {"message": "Not Found"})))


@pytest.mark.parametrize("status", [403, 429])
def test_rate_limit(status):
    with pytest.raises(UpdateError, match="busy"):
        updates.check(Http(Response(status, {})))


def test_network_failure():
    with pytest.raises(UpdateError, match="Could not reach"):
        updates.check(Http(error=requests.ConnectionError("no route")))


@pytest.mark.parametrize(
    "response",
    [Response(500, {}), Response(200, None), Response(200, {"name": "x"}),
     Response(200, {"tag_name": "nightly"}), Response(200, [1, 2])],
)
def test_unexpected_answers_do_not_crash(response):
    with pytest.raises(UpdateError, match="unexpected answer"):
        updates.check(Http(response))


def test_only_the_projects_own_pages_are_ever_opened():
    hostile = release("v9.0.0", "https://evil.example/download.exe")
    assert updates.check(Http(hostile), current="0.3.0").url == f"{PROJECT_URL}/releases"
    lookalike = release("v9.0.0", "https://github.com/inowakowski/KeyEnroll-evil/releases/tag/v9")
    assert updates.check(Http(lookalike), current="0.3.0").url == f"{PROJECT_URL}/releases"
