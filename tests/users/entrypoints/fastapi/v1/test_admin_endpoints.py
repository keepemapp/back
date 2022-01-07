import pytest
from fastapi.routing import APIRoute

from tests.users.entrypoints.fastapi import *


@pytest.mark.unit
class TestAdminEndpoints:
    def test_user_denied(self, app, user_client):
        api_rs = [r for r in app.routes if isinstance(r, APIRoute)]
        admin_routes = [r for r in api_rs if "admin" in r.tags]
        for r in admin_routes:
            for method in r.methods:
                resp = user_client.request(method, r.path)
                assert resp.status_code == 403

    def test_admin_allowed(self, app, admin_client):
        api_rs = [r for r in app.routes if isinstance(r, APIRoute)]
        admin_routes = [r for r in api_rs if "admin" in r.tags]
        for r in admin_routes:
            for method in r.methods:
                resp = admin_client.request(method, r.path)
                assert resp.status_code != 403
