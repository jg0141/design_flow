#!/usr/bin/env python3
"""Decrypt / encrypt data.json of the Design Flow site.

  python tools/crypt.py decrypt data.json plain.json    # -> editable JSON (never commit plain.json)
  python tools/crypt.py encrypt plain.json data.json    # -> encrypted data.json to commit

Format: gzip(JSON) -> AES-256-GCM, key = PBKDF2-HMAC-SHA256(password, salt, iter).
Needs: pip install cryptography
"""
import base64, getpass, gzip, hashlib, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITER = 250000


def key_for(pw, salt, it):
    return hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, it, 32)


def decrypt(src, dst, pw):
    enc = json.load(open(src, encoding='utf-8'))
    key = key_for(pw, base64.b64decode(enc['salt']), enc['iter'])
    data = gzip.decompress(AESGCM(key).decrypt(base64.b64decode(enc['iv']), base64.b64decode(enc['ct']), None))
    json.dump(json.loads(data), open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def encrypt(src, dst, pw):
    data = json.load(open(src, encoding='utf-8'))
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(key_for(pw, salt, ITER)).encrypt(iv, gzip.compress(json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()), None)
    b = lambda x: base64.b64encode(x).decode()
    json.dump({'v': 1, 'iter': ITER, 'salt': b(salt), 'iv': b(iv), 'ct': b(ct)}, open(dst, 'w', encoding='utf-8'))


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in ('decrypt', 'encrypt'):
        sys.exit(__doc__)
    pw = os.environ.get('DESIGN_FLOW_PASSWORD') or getpass.getpass('password: ')
    (decrypt if sys.argv[1] == 'decrypt' else encrypt)(sys.argv[2], sys.argv[3], pw)
    print('ok ->', sys.argv[3])
