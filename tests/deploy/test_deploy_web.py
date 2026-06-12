"""Tests for the deploy dashboard base-injection (deploy.web)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from deploy.web import _effective_prefix, _render_index, setup_web

TEMPLATE = '<html><head><title>x</title></head><body><img src="/__APP_BASE__/a.js"></body></html>'


def _request(headers=None, app_root_path: str = "") -> Request:
    return Request({"type": "http", "headers": headers or [], "app_root_path": app_root_path})


def test_effective_prefix_from_header():
    req = _request(headers=[(b"x-forwarded-prefix", b"/cloudapi-deploy")])
    assert _effective_prefix(req) == "/cloudapi-deploy"


def test_effective_prefix_strips_trailing_slash():
    req = _request(headers=[(b"x-forwarded-prefix", b"/cloudapi-deploy/")])
    assert _effective_prefix(req) == "/cloudapi-deploy"


def test_effective_prefix_empty_for_direct():
    assert _effective_prefix(_request()) == ""


def test_render_index_direct_mode():
    html = _render_index(TEMPLATE, _request())
    assert "/app/a.js" in html
    assert "/__APP_BASE__/" not in html
    assert 'window.__API_BASE__=""' in html
    assert 'window.__APP_BASE__="/app"' in html


def test_render_index_gateway_mode():
    req = _request(headers=[(b"x-forwarded-prefix", b"/cloudapi-deploy")])
    html = _render_index(TEMPLATE, req)
    assert "/cloudapi-deploy/app/a.js" in html
    assert 'window.__API_BASE__="/cloudapi-deploy"' in html
    assert html.index("__API_BASE__") < html.index("</head>")


def test_setup_web_serves_dashboard():
    app = FastAPI()
    setup_web(app)
    client = TestClient(app)
    res = client.get("/app")
    assert res.status_code == 200
    assert "Monohelper Deploy" in res.text
    assert "window.__API_BASE__" in res.text
