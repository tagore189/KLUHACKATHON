"""MongoDB database connection and user management utilities."""
import os
import bcrypt
from datetime import datetime, timezone
from pymongo import MongoClient, errors
from pymongo.collection import Collection

_client: MongoClient | None = None
_db = None


def get_db():
    """Return the database instance, creating the client if needed."""
    global _client, _db
    if _db is None:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
        db_name   = os.environ.get('MONGO_DB',  'visionclaim')
        _client   = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        _db       = _client[db_name]
        # Ensure unique email index
        _db.users.create_index('email', unique=True)
    return _db


def get_users() -> Collection:
    return get_db().users


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt())


def check_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed)


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(first_name: str, last_name: str, email: str, password: str) -> dict:
    """
    Insert a new user document. Returns the created user dict (without password).
    Raises ValueError if email already exists.
    """
    email = email.lower().strip()
    users = get_users()

    if users.find_one({'email': email}):
        raise ValueError('An account with this email already exists.')

    doc = {
        'first_name':  first_name.strip(),
        'last_name':   last_name.strip(),
        'email':       email,
        'password':    hash_password(password),
        'created_at':  datetime.now(timezone.utc),
        'last_login':  None,
    }
    result = users.insert_one(doc)
    doc['_id'] = result.inserted_id
    return _safe(doc)


def find_user_by_email(email: str) -> dict | None:
    """Return a full user document (including hashed password) or None."""
    return get_users().find_one({'email': email.lower().strip()})


def verify_user(email: str, password: str) -> dict | None:
    """
    Verify credentials. Returns a safe user dict (no password) on success,
    or None on failure.
    """
    user = find_user_by_email(email)
    if not user:
        return None
    if not check_password(password, user['password']):
        return None

    # Update last_login
    get_users().update_one(
        {'_id': user['_id']},
        {'$set': {'last_login': datetime.now(timezone.utc)}}
    )
    return _safe(user)


def _safe(user: dict) -> dict:
    """Strip sensitive fields and convert ObjectId to string."""
    return {
        'id':         str(user.get('_id', '')),
        'email':      user.get('email', ''),
        'first_name': user.get('first_name', ''),
        'last_name':  user.get('last_name', ''),
        'name':       f"{user.get('first_name','')} {user.get('last_name','')}".strip(),
        'created_at': str(user.get('created_at', '')),
    }
