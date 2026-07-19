import os

from app import create_app


def setup_module(module):
    os.environ["FLASK_ENV"] = "testing"


def test_project_routes_available():
    app = create_app()
    client = app.test_client()

    response = client.get("/admin/projects")
    assert response.status_code in (200, 302)

    response = client.get("/admin/projects/create")
    assert response.status_code in (200, 302)

    response = client.get("/admin/projects/edit/1")
    assert response.status_code in (200, 302)
