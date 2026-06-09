"""Unit tests for the SPA base-injection logic in src/web.py."""

from starlette.requests import Request

from web import _effective_prefix, _render_index

TEMPLATE = '<html><head><title>x</title></head><body><img src="/__APP_BASE__/a.js"></body></html>'


def _request(headers: list[tuple[bytes, bytes]] | None = None, app_root_path: str = "") -> Request:
    return Request(
        {
            "type": "http",
            "headers": headers or [],
            "app_root_path": app_root_path,
        }
    )


def test_effective_prefix_from_header():
    req = _request(headers=[(b"x-forwarded-prefix", b"/cloudapi")])
    assert _effective_prefix(req) == "/cloudapi"


def test_effective_prefix_strips_trailing_slash():
    req = _request(headers=[(b"x-forwarded-prefix", b"/cloudapi/")])
    assert _effective_prefix(req) == "/cloudapi"


def test_effective_prefix_falls_back_to_scope():
    req = _request(app_root_path="/cloudapi")
    assert _effective_prefix(req) == "/cloudapi"


def test_effective_prefix_empty_for_direct_access():
    assert _effective_prefix(_request()) == ""


def test_render_index_direct_mode():
    html = _render_index(TEMPLATE, _request())
    assert "/app/a.js" in html  # placeholder rewritten
    assert "/__APP_BASE__/" not in html
    assert 'window.__API_BASE__=""' in html
    assert 'window.__APP_BASE__="/app"' in html


def test_render_index_gateway_mode():
    req = _request(headers=[(b"x-forwarded-prefix", b"/cloudapi")])
    html = _render_index(TEMPLATE, req)
    assert "/cloudapi/app/a.js" in html
    assert 'window.__API_BASE__="/cloudapi"' in html
    assert 'window.__APP_BASE__="/cloudapi/app"' in html
    # injected before </head>
    assert html.index("__API_BASE__") < html.index("</head>")
