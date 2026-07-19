import io
import urllib.request
from app import app
from model import db, Profile

png = bytes([137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82,0,0,0,1,0,0,0,1,8,2,0,0,0,144,119,83,222,0,0,0,10,73,68,65,84,120,156,99,96,0,0,0,2,0,1,226,33,188,51,0,0,0,0,73,69,78,68,174,66,96,130])

with app.test_client() as client:
    login = client.post('/login', data={'username':'admin','password':'admin123'}, follow_redirects=True)
    print('login.status', login.status_code)
    print('login.path', getattr(login.request, 'path', None))
    if b'Username atau Password salah' in login.data:
        raise SystemExit('Login failed in test client')

    data = {
        'nama_lengkap': 'Test Upload',
        'nama_panggilan': 'TU',
        'tempat_lahir': 'Jakarta',
        'tanggal_lahir': '2000-01-01',
        'email': 'testupload@example.com',
        'telepon': '0812345678',
        'universitas': 'ITB',
        'fakultas': 'Teknik',
        'prodi': 'Informatika',
        'semester': '8',
        'alamat': 'Alamat test',
    }
    data['foto_profil'] = (io.BytesIO(png), 'test.png')
    create = client.post('/admin/profile/create', data=data, content_type='multipart/form-data', follow_redirects=False)
    print('create.status', create.status_code)
    print('create.location', create.headers.get('Location'))
    print('create.body', create.get_data(as_text=True)[:500])

    with app.app_context():
        latest = db.session.query(Profile).order_by(Profile.id.desc()).first()
        if latest is None:
            raise SystemExit('No profile row found after create')
        print('db.id', latest.id)
        print('db.nama_lengkap', latest.nama_lengkap)
        print('db.foto_url', latest.foto_url)
        if latest.foto_url and latest.foto_url.startswith('http'):
            try:
                req = urllib.request.Request(latest.foto_url, method='HEAD')
                resp = urllib.request.urlopen(req, timeout=20)
                print('url.status', resp.status)
            except Exception as e:
                print('url.check.fail', e)
