"""
One-time migration: SQLite dev.db → Firestore
Run: python scripts/migrate_to_firestore.py
"""

import sys, os, json, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.firestore_client import FirestoreClient

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'dev.db')


def migrate_table(db, conn, table, collection, id_field, transform=None):
    """Migrate one SQLite table to a Firestore collection."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    print(f"  {table}: {len(rows)} rows -> {collection}")
    
    if transform is None:
        transform = lambda r: r
    
    batch = []
    for row in rows:
        data = {k: row[k] for k in row.keys()}
        doc_id = str(data.pop(id_field)) if id_field in data else None
        if transform:
            data = transform(data)
        data = {k: v for k, v in data.items() if v is not None}
        data['_id'] = doc_id
        batch.append(data)
    
    db.batch_write(collection, batch)
    print(f"  Done: {len(batch)} documents")


def main():
    print("=" * 60)
    print("  PDF Website -- SQLite to Firestore Migration")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    db = FirestoreClient()
    
    # Get all table names
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    print(f"\nFound {len(tables)} tables: {', '.join(tables)}\n")
    
    # Migrate core tables
    migrations = [
        ('districts', 'districts', 'code'),
        ('cases', 'cases', 'case_id'),
        ('articles', 'articles', 'slug'),
        ('speeches', 'speeches', 'video_id'),
        ('resources', 'resources', 'id', lambda d: d.update({'_id': str(d.pop('id'))}) or d),
        ('updates', 'updates', 'id', lambda d: d.update({'_id': str(d.pop('id'))}) or d),
        ('system_config', 'config', 'config_key'),
    ]
    
    for table, collection, id_field, *rest in migrations:
        transform = rest[0] if rest else None
        try:
            migrate_table(db, conn, table, collection, id_field, transform)
        except Exception as e:
            print(f"  ERROR migrating {table}: {e}")
    
    # Migrate restraint_data in batches (large table)
    print("\n--- Restraint Data (large table, batched) ---")
    conn.row_factory = sqlite3.Row
    total = conn.execute("SELECT COUNT(*) FROM restraint_data").fetchone()[0]
    print(f"  restraint_data: {total} rows -> restraint_data")
    
    offset = 0
    batch_size = 500
    migrated = 0
    while offset < total:
        rows = conn.execute(
            "SELECT * FROM restraint_data LIMIT ? OFFSET ?",
            (batch_size, offset)
        ).fetchall()
        batch = []
        for row in rows:
            data = {k: row[k] for k in row.keys() if k != 'id'}
            data = {k: v for k, v in data.items() if v is not None}
            # Use school_code + school_year as document ID for deduplication
            sc = data.get('school_code', 'unknown')
            sy = data.get('school_year', 'unknown')
            data['_id'] = f"{sc}_{sy}"
            batch.append(data)
        db.batch_write('restraint_data', batch)
        migrated += len(batch)
        offset += batch_size
        print(f"  {migrated}/{total} documents migrated...")
    
    print(f"\n  Done: {migrated} restraint documents")
    conn.close()
    
    # List Firestore collections
    print("\n--- Firestore Collections ---")
    for col in db.db.collections():
        docs = len(list(col.limit(5).stream()))
        print(f"  {col.id}: {docs}+ docs")
    
    print("\nMigration complete!")


if __name__ == '__main__':
    main()
