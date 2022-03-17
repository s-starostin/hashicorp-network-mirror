import hashlib
from base64 import b64encode
from zipfile import ZipFile

def hash_zip(filepath):
    h1 = hashlib.sha256()

    with ZipFile(filepath, 'r') as zf:
        for zfilename in zf.namelist():
            with zf.open(zfilename) as f:
                h = hashlib.sha256()
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    h.update(chunk)
                h1.update((str(h.hexdigest()) + "  " + f.name + "\n").encode("utf-8"))

    return "h1:" + (b64encode(h1.digest())).decode("utf-8")
