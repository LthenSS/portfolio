from app import app
from model import Contact

client = app.test_client()
resp = client.post(
    '/contact',
    data={
        'nama': 'Test Contact',
        'email': 'test@example.com',
        'subjek': 'Tes Resend',
        'pesan': 'Ini pesan tes contact.',
    },
    follow_redirects=True,
)
print('status', resp.status_code)
text = resp.get_data(as_text=True)
print('flash-pesan', 'Pesan berhasil dikirim.' in text)
print('flash-email', 'Email berhasil dikirim.' in text)

with app.app_context():
    last = Contact.query.order_by(Contact.id.desc()).first()
    if last:
        print('last-contact', last.id, last.nama, last.email, last.subjek)
    else:
        print('last-contact', None)
