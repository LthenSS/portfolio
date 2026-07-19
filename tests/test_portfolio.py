from app import app


def test_portfolio_index():
    """Pastikan halaman portfolio publik dapat diakses."""
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b'id="hero"' in response.data
    assert b'id="about"' in response.data
    assert b'id="skills"' in response.data
    assert b'id="experience"' in response.data
    assert b'id="projects"' in response.data
    assert b'id="contact"' in response.data
