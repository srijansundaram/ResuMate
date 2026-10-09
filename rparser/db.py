import json
import sqlite3

DB = "resumes.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS candidates(
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, name TEXT,
        data TEXT, status TEXT DEFAULT 'new', tags TEXT DEFAULT '',
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    return c


def save(filename: str, parsed: dict) -> int:
    with _conn() as c:
        cur = c.execute("INSERT INTO candidates(filename,name,data) VALUES(?,?,?)",
                        (filename, parsed.get("name"), json.dumps(parsed)))
        return cur.lastrowid


def all_candidates() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT id,filename,data,status,tags FROM candidates").fetchall()
    out = []
    for id_, fn, data, status, tags in rows:
        d = json.loads(data)
        d.update(id=id_, filename=fn, status=status, tags=tags)
        out.append(d)
    return out


def set_status(cid: int, status: str, tags: str = ""):
    with _conn() as c:
        c.execute("UPDATE candidates SET status=?, tags=? WHERE id=?", (status, tags, cid))


def delete(cid: int):
    with _conn() as c:
        c.execute("DELETE FROM candidates WHERE id=?", (cid,))

def clear_all():
    with _conn() as c:
        c.execute("DELETE FROM candidates")