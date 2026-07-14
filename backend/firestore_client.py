"""
Parent Data Force — Firestore Client
=====================================
Replaces SQLite with Firestore for cloud-hosted mode.
Uses service account key or Application Default Credentials.

Usage:
    from backend.firestore_client import FirestoreClient
    db = FirestoreClient()
    docs = db.query('restraint_data', filters=[('school_year', '==', '2024-25')])
"""

import os
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore

ROOT = Path(__file__).resolve().parent.parent
KEY_PATH = Path(os.environ.get(
    "FIRESTORE_KEY_PATH",
    ROOT.parent / "firebase-key.json"
))

_app_initialized = False
_db_client = None


def init_firestore(key_path: str = None) -> firestore.Client:
    global _app_initialized, _db_client
    if _app_initialized:
        return _db_client

    if key_path is None:
        key_path = str(KEY_PATH)

    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

    _db_client = firestore.client()
    _app_initialized = True
    return _db_client


class FirestoreClient:
    """Wrapper around Firestore for the PDF website data access patterns."""

    def __init__(self):
        self.db = init_firestore()

    def collection(self, name: str):
        return self.db.collection(name)

    def get_all(self, collection: str, order_by: str = None,
                direction: str = 'ASCENDING', limit: int = None):
        ref = self.db.collection(collection)
        if order_by:
            d = firestore.Query.ASCENDING if direction == 'ASCENDING' else firestore.Query.DESCENDING
            ref = ref.order_by(order_by, direction=d)
        if limit:
            ref = ref.limit(limit)
        return [doc.to_dict() | {'_id': doc.id} for doc in ref.stream()]

    def get_doc(self, collection: str, doc_id: str):
        doc = self.db.collection(collection).document(doc_id).get()
        if doc.exists:
            return doc.to_dict() | {'_id': doc.id}
        return None

    def set_doc(self, collection: str, doc_id: str, data: dict, merge: bool = True):
        self.db.collection(collection).document(doc_id).set(data, merge=merge)

    def query(self, collection: str, filters: list = None,
              order_by: str = None, direction: str = 'ASCENDING',
              limit: int = None, offset: int = 0):
        ref = self.db.collection(collection)
        if filters:
            for field, op, value in filters:
                ref = ref.where(filter=firestore.FieldFilter(field, op, value))
        if order_by:
            d = firestore.Query.ASCENDING if direction == 'ASCENDING' else firestore.Query.DESCENDING
            ref = ref.order_by(order_by, direction=d)
        if limit:
            ref = ref.limit(limit)
        if offset:
            ref = ref.offset(offset)
        return [doc.to_dict() | {'_id': doc.id} for doc in ref.stream()]

    def query_count(self, collection: str, filters: list = None) -> int:
        ref = self.db.collection(collection)
        if filters:
            for field, op, value in filters:
                ref = ref.where(filter=firestore.FieldFilter(field, op, value))
        # Firestore doesn't have COUNT natively in older clients; use aggregation query
        aggr = ref.count()
        return next(aggr.stream())[0].value

    def delete_collection(self, collection: str, batch_size: int = 500):
        docs = self.db.collection(collection).limit(batch_size).stream()
        deleted = 0
        for doc in docs:
            doc.reference.delete()
            deleted += 1
        if deleted >= batch_size:
            return self.delete_collection(collection, batch_size)

    def batch_write(self, collection: str, docs: list[dict], id_field: str = '_id'):
        batch = self.db.batch()
        count = 0
        for doc_data in docs:
            doc_id = doc_data.pop(id_field, None)
            data = {k: v for k, v in doc_data.items() if v is not None}
            if doc_id:
                ref = self.db.collection(collection).document(doc_id)
            else:
                ref = self.db.collection(collection).document()
            batch.set(ref, data)
            count += 1
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0
        if count > 0:
            batch.commit()

    def get_distinct_values(self, collection: str, field: str) -> list:
        docs = self.get_all(collection, order_by=field)
        seen = set()
        result = []
        for d in docs:
            val = d.get(field)
            if val and val not in seen:
                seen.add(val)
                result.append(val)
        return result
