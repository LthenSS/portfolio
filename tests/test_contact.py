from app import app


def setup_module(module):
    pass


def test_contact_routes():
    client = app.test_client()

    # 1. Public contact form
    response = client.get("/contact")
    assert response.status_code == 200

    # 2. Create contact
    response = client.post(
        "/contact",
        data={
            "nama": "Test User",
            "email": "test@example.com",
            "subjek": "Halo",
            "pesan": "Pesan percobaan",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # 3. Admin login and list
    client.post("/login", data={"username": "admin", "password": "admin123"})
    list_resp = client.get("/admin/contacts")
    assert list_resp.status_code == 200

    # 4. Admin view first contact
    view_resp = client.get("/admin/contacts/1")
    assert view_resp.status_code == 200

    # 5. Mark as read
    read_resp = client.post("/admin/contacts/read/1", follow_redirects=True)
    assert read_resp.status_code == 200

    # 6. Delete contact
    delete_resp = client.post("/admin/contacts/delete/1", follow_redirects=True)
    assert delete_resp.status_code == 200
