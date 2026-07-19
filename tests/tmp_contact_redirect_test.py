from app import app

client = app.test_client()
resp = client.post('/contact', data={'nama':'A','email':'a@example.com','subjek':'test','pesan':'msg'}, follow_redirects=False)
print('status', resp.status_code)
print('location', resp.headers.get('Location'))
print('location url', resp.location)
