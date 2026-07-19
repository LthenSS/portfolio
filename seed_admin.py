from werkzeug.security import generate_password_hash

from model import Database


def seed_admin():
    """Membuat akun admin default atau reset password admin jika sudah ada."""
    db = Database()
    query = "SELECT id FROM users WHERE username = %s"
    existing = db.execute_query(query, ("admin",), fetch=True)

    password_hash = generate_password_hash("admin123")

    if existing:
        update_query = "UPDATE users SET password_hash = %s WHERE username = %s"
        db.execute_query(update_query, (password_hash, "admin"), fetch=False)
        print("Password admin berhasil direset.")
        return

    insert_query = """
    INSERT INTO users (username, password_hash, role, created_at)
    VALUES (%s, %s, %s, NOW())
    """
    db.execute_query(insert_query, ("admin", password_hash, "admin"), fetch=False)
    print("Password admin berhasil direset.")


if __name__ == "__main__":
    seed_admin()
