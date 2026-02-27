"""MongoDB database connection and user management utilities."""
import os
import uuid
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


# ── Scan Persistence ──────────────────────────────────────────────────────────

def save_scan(user_id: str, scan_data: dict) -> str:
    """Save a scan report for a user."""
    db = get_db()
    
    # Use report_id from AI if available, else generate unique one
    scan_id = scan_data.get('report_id') or f"SCAN-{uuid.uuid4().hex[:12].upper()}"
    
    # Correctly access damage_assessment from report
    assessment = scan_data.get('damage_assessment', {})
    overall_severity = assessment.get('overall_severity', 'minor').lower()
    
    scan_doc = {
        'user_id': user_id,
        'scan_id': scan_id,
        'data': scan_data,
        'created_at': datetime.now(timezone.utc),
        'status': 'Under Review' if overall_severity == 'severe' else 'Completed'
    }
    result = db.scans.insert_one(scan_doc)
    return str(result.inserted_id)


def get_user_scans(user_id: str):
    """Retrieve all scans for a specific user, newest first."""
    db = get_db()
    return list(db.scans.find({'user_id': user_id}).sort('created_at', -1))


def get_scan(scan_id: str, user_id: str = None):
    """Retrieve a specific scan by its database ID."""
    from bson.objectid import ObjectId
    db = get_db()
    query = {'_id': ObjectId(scan_id)}
    if user_id:
        query['user_id'] = user_id
    return db.scans.find_one(query)


def get_scan_by_report_id(report_id: str, user_id: str = None):
    """Retrieve a scan by its report_id."""
    db = get_db()
    query = {'data.report_id': report_id}
    if user_id:
        query['user_id'] = user_id
    return db.scans.find_one(query)


def save_claim(claim_data: dict) -> str:
    """Save an official insurance claim."""
    db = get_db()
    claim_id = f"CLM-{datetime.now().strftime('%y%m%d%H%M%S')}"
    claim_doc = {
        'claim_id': claim_id,
        'report_id': claim_data.get('report_id'),
        'user_id': claim_data.get('user_id'),
        'policy_number': claim_data.get('policy_number'),
        'license_plate': claim_data.get('license_plate'),
        'owner_name': claim_data.get('owner_name'),
        'incident': {
            'date': claim_data.get('incident_date'),
            'location': claim_data.get('incident_location'),
            'description': claim_data.get('incident_description')
        },
        'status': 'Submitted',
        'submitted_at': datetime.now(timezone.utc)
    }
    result = db.claims.insert_one(claim_doc)
    return claim_id


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
