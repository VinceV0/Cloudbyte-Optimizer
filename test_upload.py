import urllib.request
import json

boundary = '----WebKitFormBoundaryXYZ'
body = (
    b'--' + boundary.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
    b'Content-Type: text/plain\r\n\r\n'
    + (b'The quick brown fox jumps over the lazy dog\n' * 500)
    + b'\r\n--' + boundary.encode() + b'--\r\n'
)

req = urllib.request.Request(
    'http://127.0.0.1:8080/api/benchmark',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        results = data.get('results', [])
        print(f'Server returned {len(results)} algorithms:')
        for r in results:
            print(' ', r['key'], r['name'])
except Exception as e:
    print('Request error:', e)
