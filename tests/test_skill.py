from app import app


def run_skill_tests():
    """Uji alur CRUD Skill sederhana untuk admin."""
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    # 1. Tampilkan daftar skill
    list_resp = client.get("/admin/skills")
    print("LIST", list_resp.status_code)

    # 2. Buka form tambah skill
    create_form = client.get("/admin/skills/create")
    print("CREATE_FORM", create_form.status_code)

    # 3. Simpan skill baru
    create_resp = client.post(
        "/admin/skills/create",
        data={
            "nama_skill": "TestSkill",
            "icon_class": "fa-brands fa-python",
        },
        follow_redirects=True,
    )
    print("CREATE", create_resp.status_code)

    # 4. Tampilkan daftar skill lagi
    list_resp = client.get("/admin/skills")
    print("LIST_AFTER_CREATE", list_resp.status_code)

    # 5. Buka form edit skill
    skill_id = next(iter(app.config.get("_skill_store", {}).keys()), "1")
    skill_id = int(skill_id)
    edit_form_resp = client.get(f"/admin/skills/edit/{skill_id}")
    print("EDIT_FORM", edit_form_resp.status_code)

    # 6. Simpan perubahan skill
    edit_resp = client.post(
        f"/admin/skills/edit/{skill_id}",
        data={
            "nama_skill": "TestSkillUpdated",
            "icon_class": "fa-brands fa-python",
        },
        follow_redirects=True,
    )
    print("EDIT", edit_resp.status_code)

    # 7. Hapus skill
    delete_resp = client.post(f"/admin/skills/delete/{skill_id}", follow_redirects=True)
    print("DELETE", delete_resp.status_code)


if __name__ == "__main__":
    run_skill_tests()
