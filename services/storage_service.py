from pathlib import Path
import sqlite3
import json

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "field_tests.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT UNIQUE, officer_id TEXT, drug TEXT, batch TEXT,
        result TEXT, confidence REAL, timestamp TEXT,
        latitude REAL, longitude REAL, image_hash TEXT, record_hash TEXT,
        explanation TEXT, cv_data TEXT)""")
    c.commit(); c.close()

def save_test(t):
    c = conn()
    c.execute("""INSERT INTO tests
        (record_id,officer_id,drug,batch,result,confidence,timestamp,latitude,longitude,
         image_hash,record_hash,explanation,cv_data)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (t["record_id"],t["officer_id"],t["drug"],t["batch"],t["result"],t["confidence"],
         t["timestamp"],t.get("latitude"),t.get("longitude"),t["image_hash"],
         t["record_hash"],t["explanation"],json.dumps(t.get("cv_data",{}))))
    c.commit(); c.close()

def list_tests(search=""):
    c = conn()
    if search:
        q = f"%{search}%"
        rows = c.execute("""SELECT * FROM tests
          WHERE record_id LIKE ? OR officer_id LIKE ? OR drug LIKE ? OR result LIKE ? OR batch LIKE ?
          ORDER BY id DESC""",(q,q,q,q,q)).fetchall()
    else:
        rows = c.execute("SELECT * FROM tests ORDER BY id DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]
