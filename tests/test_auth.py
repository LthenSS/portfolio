from app import app


def run_tests():
    """Script sederhana untuk menguji alur auth admin."""
    with app.test_client() as client:
        # 1. Login berhasil.
        response = client.post(
            "/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )
        print("LOGIN_OK", response.status_code)

        # 2. Login gagal.
        response = client.post(
            "/login",
            data={"username": "admin", "password": "salah"},
            follow_redirects=True,
        )
        print("LOGIN_FAIL", response.status_code)

        # 3. Logout.
        response = client.get("/logout", follow_redirects=True)
        print("LOGOUT_OK", response.status_code)

        # 4. Cek session.
        response = client.get("/admin/dashboard", follow_redirects=True)
        print("SESSION_CHECK", response.status_code)


if __name__ == "__main__":
    run_tests()
