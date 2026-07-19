from app import app


def run_profile_tests():
    """Uji alur CRUD Profile sederhana untuk admin."""
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    # 1. Tampilkan daftar profile
    list_resp = client.get("/admin/profile")
    print("LIST", list_resp.status_code)

    # 2. Buka form tambah profile
    create_form = client.get("/admin/profile/create")
    print("CREATE_FORM", create_form.status_code)

    # 3. Simpan profile baru
    create_resp = client.post(
        "/admin/profile/create",
        data={
            "nama_lengkap": "Test User",
            "nama_panggilan": "Test",
            "tempat_lahir": "Bandung",
            "tanggal_lahir": "2000-01-01",
            "email": "test@example.com",
            "telepon": "081234567890",
            "universitas": "Universitas Test",
            "fakultas": "Teknik",
            "prodi": "Informatika",
            "semester": "6",
            "alamat": "Jakarta",
        },
        follow_redirects=True,
    )
    print("CREATE", create_resp.status_code)

    # 4. Tampilkan daftar profile lagi
    list_resp = client.get("/admin/profile")
    print("LIST_AFTER_CREATE", list_resp.status_code)

    # 5. Buka form edit profile
    profile_id = next(iter(app.config.get("_profile_store", {}).keys()), "1")
    profile_id = int(profile_id)
    edit_form_resp = client.get(f"/admin/profile/edit/{profile_id}")
    print("EDIT_FORM", edit_form_resp.status_code)

    # 6. Simpan perubahan profile
    edit_resp = client.post(
        f"/admin/profile/edit/{profile_id}",
        data={
            "nama_lengkap": "Test User Updated",
            "nama_panggilan": "Test",
            "tempat_lahir": "Bandung",
            "tanggal_lahir": "2000-01-01",
            "email": "updated@example.com",
            "telepon": "081234567890",
            "universitas": "Universitas Test",
            "fakultas": "Teknik",
            "prodi": "Informatika",
            "semester": "6",
            "alamat": "Jakarta",
        },
        follow_redirects=True,
    )
    print("EDIT", edit_resp.status_code)

    # 7. Hapus profile
    delete_resp = client.post(f"/admin/profile/delete/{profile_id}", follow_redirects=True)
    print("DELETE", delete_resp.status_code)


if __name__ == "__main__":
    run_profile_tests()
