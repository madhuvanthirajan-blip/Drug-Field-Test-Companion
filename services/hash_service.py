import hashlib
import json

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def record_hash(record):
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()
