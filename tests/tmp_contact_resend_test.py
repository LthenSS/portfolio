from config import Config
from Backend.admin.contact import _send_contact_email
from app import app
from model import Contact

print('RESEND_API_KEY:', bool(Config.RESEND_API_KEY), repr(Config.RESEND_API_KEY))
print('RESEND_FROM:', bool(Config.RESEND_FROM), repr(Config.RESEND_FROM))
print('EMAIL_PENERIMA:', bool(Config.EMAIL_PENERIMA), repr(Config.EMAIL_PENERIMA))

print('\n--- Direct helper test ---')
sent, error = _send_contact_email(
    nama='Test Contact',
    email='test@example.com',
    subjek='Tes Resend',
    pesan='Ini adalah pengujian email dari aplikasi portfolio.',
)
print('helper sent:', sent)
print('helper error:', repr(error))

print('\n--- Public form submit test ---')
client = app.test_client()
resp = client.post(
    '/contact',
    data={
        'nama': 'Test Contact',
        'email': 'test@example.com',
        'subjek': 'Tes Resend',
        'pesan': 'Ini adalah pengujian email dari aplikasi portfolio.',
    },
    follow_redirects=True,
)
print('form status_code:', resp.status_code)
text = resp.get_data(as_text=True)
print('form contains Pesan berhasil dikirim.:', 'Pesan berhasil dikirim.' in text)
print('form contains Email berhasil dikirim.:', 'Email berhasil dikirim.' in text)
print('form response snippet:', text[:400].replace('\n', ' '))

with app.app_context():
    contact = Contact.query.filter_by(email='test@example.com', subjek='Tes Resend').order_by(Contact.id.desc()).first()
    print('db contact found:', bool(contact))
    if contact:
        print('contact id:', contact.id)
        print('contact nama:', contact.nama)
        print('contact email:', contact.email)
        print('contact subjek:', contact.subjek)
        print('contact status:', contact.status)
