from app import app


def run_experience_tests():
    """Uji alur CRUD Experience sederhana untuk admin."""
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    # 1. Tampilkan daftar experience
    list_resp = client.get("/admin/experiences")
    print("LIST", list_resp.status_code)

    # 2. Buka form tambah experience
    create_form = client.get("/admin/experiences/create")
    print("CREATE_FORM", create_form.status_code)

    # 3. Simpan experience baru
    create_resp = client.post(
        "/admin/experiences/create",
        data={
            "posisi": "Developer",
            "perusahaan": "ACME",
            "durasi": "1 tahun",
            "deskripsi": "Deskripsi pengalaman",
        },
        follow_redirects=True,
    )
    print("CREATE", create_resp.status_code)

    # 4. Tampilkan daftar experience lagi
    list_resp = client.get("/admin/experiences")
    print("LIST_AFTER_CREATE", list_resp.status_code)

    # 5. Buka form edit experience
    exp_id = next(iter(app.config.get("_experience_store", {}).keys()), "1")
    exp_id = int(exp_id)
    edit_form_resp = client.get(f"/admin/experiences/edit/{exp_id}")
    print("EDIT_FORM", edit_form_resp.status_code)

    # 6. Simpan perubahan experience
    edit_resp = client.post(
        f"/admin/experiences/edit/{exp_id}",
        data={
            "posisi": "Developer Updated",
            "perusahaan": "ACME",
            "durasi": "2 tahun",
            "deskripsi": "Deskripsi updated",
        },
        follow_redirects=True,
    )
    print("EDIT", edit_resp.status_code)

    # 7. Hapus experience
    delete_resp = client.post(f"/admin/experiences/delete/{exp_id}", follow_redirects=True)
    print("DELETE", delete_resp.status_code)


if __name__ == "__main__":
    run_experience_tests()
