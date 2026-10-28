"""Snapshots imutáveis em SQLite local; cada salvamento preserva versão anterior."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,sqlite3
DB=Path(__file__).resolve().parent/'data'/'local.sqlite3'


def connect(path=None):
    p=Path(path or os.environ.get('PET_CIRCULAR_DB',str(DB)))
    p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(p,timeout=5)
    c.row_factory=sqlite3.Row
    c.execute('''CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, product_id TEXT NOT NULL,
        design_version TEXT NOT NULL, product_name TEXT NOT NULL, saved_at TEXT NOT NULL,
        envelope TEXT NOT NULL, result_json TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS ix_snapshots ON snapshots (project_id,product_id,design_version,id)')
    c.commit();return c


def save(product,result=None,path=None):
    with connect(path) as c:
        row=c.execute('''INSERT INTO snapshots (project_id,product_id,design_version,product_name,saved_at,envelope,result_json)
         VALUES (?,?,?,?,?,?,?)''',(product['project_id'],product['product_id'],product.get('design_version','v1'),
           product['product_name'],datetime.now(timezone.utc).isoformat(timespec='seconds'),
           json.dumps(product,ensure_ascii=False),json.dumps(result,ensure_ascii=False) if result is not None else None))
        return row.lastrowid


def latest(path=None):
    with connect(path) as c:
        rows=c.execute('''SELECT id,project_id,product_id,design_version,product_name,saved_at FROM snapshots s
         WHERE id=(SELECT MAX(id) FROM snapshots t WHERE t.project_id=s.project_id AND t.product_id=s.product_id
         AND t.design_version=s.design_version) ORDER BY id DESC LIMIT 200''').fetchall()
    return [dict(r) for r in rows]


def load(snapshot_id,path=None):
    with connect(path) as c:
        r=c.execute('SELECT envelope,result_json FROM snapshots WHERE id=?',(snapshot_id,)).fetchone()
    if r is None:raise ValueError('Registro não encontrado.')
    return json.loads(r['envelope']),json.loads(r['result_json']) if r['result_json'] else None
