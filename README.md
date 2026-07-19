# Portofolio Backend - README

## Struktur Backend

Backend ini dibangun menggunakan **Flask** (Python) dengan struktur sebagai berikut:

```
Backend/
├── admin/
│   ├── __init__.py          # Package initialization
│   ├── akun.py              # Endpoint manajemen akun user
│   ├── dashboard.py         # Endpoint statistik dashboard
│   ├── experience.py        # CRUD experiences
│   ├── login.py             # Authentication & JWT token
│   ├── projects.py          # CRUD projects
│   └── skills.py            # CRUD skills
│
└── profil/
    ├── __init__.py          # Package initialization
    └── profil.py            # CRUD profil pengguna
```

## File Konfigurasi

- `config.py` - Konfigurasi aplikasi (database, secret key, dll)
- `model.py` - Database connection pool dan helper functions
- `app.py` - Main Flask application
- `.env` - Environment variables (jangan di-commit ke git!)

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/login` | Login user | No |
| POST | `/api/logout` | Logout user | Yes |
| GET | `/api/auth/check` | Cek status auth | No |

### Dashboard
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/dashboard/stats` | Statistik dashboard | Yes |
| GET | `/api/dashboard/recent-activity` | Aktivitas terbaru | Yes |

### Akun
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/akun` | Get data akun | Yes |
| PUT | `/api/akun` | Update data akun | Yes |
| POST | `/api/akun/change-password` | Ganti password | Yes |

### Profil
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/profil` | Get profil publik | No |
| POST | `/api/profil` | Create profil | Yes |
| PUT | `/api/profil` | Update profil | Yes |

### Experiences
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/experiences` | Get semua experiences | No |
| GET | `/api/experiences/<id>` | Get satu experience | No |
| POST | `/api/experiences` | Create experience | Yes |
| PUT | `/api/experiences/<id>` | Update experience | Yes |
| DELETE | `/api/experiences/<id>` | Delete experience | Yes |

### Projects
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/projects` | Get semua projects | No |
| GET | `/api/projects/<id>` | Get satu project | No |
| POST | `/api/projects` | Create project | Yes |
| PUT | `/api/projects/<id>` | Update project | Yes |
| DELETE | `/api/projects/<id>` | Delete project | Yes |

### Skills
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/skills` | Get semua skills | No |
| GET | `/api/skills/<id>` | Get satu skill | No |
| POST | `/api/skills` | Create skill | Yes |
| PUT | `/api/skills/<id>` | Update skill | Yes |
| DELETE | `/api/skills/<id>` | Delete skill | Yes |

## Instalasi

### 1. Install Dependencies

```bash
pip install flask flask-cors python-dotenv mysql-connector-python PyJWT werkzeug
```

Atau gunakan requirements.txt (jika ada):
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Edit file `.env` sesuai dengan konfigurasi database Anda:

```env
FLASK_DEBUG=True
SECRET_KEY=ganti-dengan-secret-key-yang-lebih-aman

DB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
DB_PORT=4000
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=Portofolio

CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### 3. Setup Database

Jalankan script SQL untuk membuat tabel:

```bash
mysql -h <host> -u <user> -p < database.sql
```

### 4. Jalankan Aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di `http://localhost:5000`

## Contoh Request

### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'
```

### Get Experiences (Publik)
```bash
curl http://localhost:5000/api/experiences
```

### Create Project (Butuh Auth)
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "judul": "Project Baru",
    "deskripsi": "Deskripsi project",
    "gambar_url": "https://example.com/image.jpg",
    "link_project": "https://github.com/user/project"
  }'
```

## Security Notes

1. **Password Hashing**: Password di-hash menggunakan Werkzeug (bcrypt)
2. **JWT Token**: Autentikasi menggunakan JWT dengan expiry 24 jam
3. **CORS**: Di-enable untuk development, batasi origins di production
4. **Environment Variables**: Jangan commit `.env` ke version control!

## Database Schema

Database menggunakan TiDB Cloud (MySQL compatible) dengan tabel:
- `users` - Data user/admin
- `profiles` - Profil lengkap user
- `experiences` - Pengalaman kerja/organisasi
- `projects` - Portfolio projects
- `skills` - Keahlian/tech stack

Lihat `database.sql` untuk schema lengkap.