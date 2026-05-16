"""
database.py - Database layer for E-Voting System
Demonstrates: file handling, functions, SQLite operations
"""

import sqlite3
import hashlib
import os
from models import User, Candidate, Vote, VoteResult

# Database file path
DB_FILE = "evoting.db"


# ─── Connection Helper ────────────────────────────────────────────────────────


def get_connection():
    """Create and return a SQLite database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


# ─── Initialisation ───────────────────────────────────────────────────────────


def init_db():
    """
    Initialise database tables.
    Demonstrates: file handling — creates the .db file on disk.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            student_id TEXT    UNIQUE NOT NULL,
            is_admin   INTEGER DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Create candidates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            position     TEXT NOT NULL,
            party        TEXT NOT NULL,
            description  TEXT,
            photo        TEXT DEFAULT 'default.png',
            created_at   TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create votes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            vote_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            timestamp    TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)      REFERENCES users(user_id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
            UNIQUE (user_id)           -- one vote per user
        )
    """)

    conn.commit()

    # Migrate: add google_id and avatar_url if the columns don't exist yet
    for col, definition in [
        ("google_id", "TEXT DEFAULT ''"),
        ("avatar_url", "TEXT DEFAULT ''"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.close()

    # Seed data if database is fresh
    seed_data()


def seed_data():
    """Seed default admin and sample candidates if they don't exist."""
    # Seed admin user
    if not get_user_by_email("admin@college.edu"):
        create_user("Admin", "admin@college.edu", "admin123", "ADMIN001", is_admin=True)

    # Seed sample candidates if none exist
    candidates = get_all_candidates()
    if not candidates:
        sample_candidates = [
            (
                "Anand Hipaargi",
                "President",
                "Progressive Students Front",
                "Dedicated to improving college infrastructure and student welfare. "
                "Passionate about creating an inclusive campus environment.",
            ),
            (
                "Soham Hande",
                "Vice President",
                "United Campus Alliance",
                "Focused on academic excellence and mental health awareness programs. "
                "Strong advocate for gender equality on campus.",
            ),
            (
                "Shravan Dhokale",
                "General Secretary",
                "Progressive Students Front",
                "Committed to transparent governance and student representation. "
                "Experienced in organising large-scale college events.",
            ),
            (
                "Abhay Gurgawkar",
                "Treasurer",
                "United Campus Alliance",
                "Finance major with a plan to manage college funds responsibly. "
                "Aims to reduce unnecessary expenditure and fund student activities.",
            ),
            (
                "Dhiraj Bhand",
                "Cultural Secretary",
                "Independent",
                "Arts enthusiast planning to revive cultural festivals. "
                "Believes every student deserves a platform to showcase their talent.",
            ),
        ]
        for name, position, party, desc in sample_candidates:
            create_candidate(name, position, party, desc)


# ─── Password Helpers ─────────────────────────────────────────────────────────


def hash_password(password):
    """Hash a password using SHA-256. Demonstrates: functions."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    """Verify a plain password against a stored hash."""
    return hash_password(password) == hashed


# ─── User CRUD ────────────────────────────────────────────────────────────────


def create_user(name, email, password, student_id, is_admin=False):
    """
    Insert a new user into the database.
    Demonstrates: conditions, functions.
    Returns: True on success, False if duplicate.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, student_id, is_admin) VALUES (?, ?, ?, ?, ?)",
            (name, email, hash_password(password), student_id, 1 if is_admin else 0),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def _row_to_user(row):
    """Convert a database row to a User object (includes google fields)."""
    keys = row.keys()
    return User(
        row["user_id"],
        row["name"],
        row["email"],
        row["password"],
        row["student_id"],
        row["is_admin"],
        row["created_at"],
        google_id=row["google_id"] if "google_id" in keys else "",
        avatar_url=row["avatar_url"] if "avatar_url" in keys else "",
    )


def get_user_by_email(email):
    """Fetch a User object by email address."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def get_user_by_id(user_id):
    """Fetch a User object by primary key."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def get_all_users():
    """Return a list of all User objects. Demonstrates: loops."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_user(row) for row in rows]


def create_google_user(name, email, google_id, avatar_url, student_id):
    """
    Insert a user authenticated via Google OAuth.
    Uses a random placeholder password since they sign in with Google.
    Returns True on success, False on duplicate.
    """
    import secrets

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO users (name, email, password, student_id, is_admin, google_id, avatar_url)
               VALUES (?, ?, ?, ?, 0, ?, ?)""",
            (
                name,
                email,
                hash_password(secrets.token_hex(16)),
                student_id,
                google_id,
                avatar_url,
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_google_user(user_id, google_id, avatar_url):
    """Refresh Google ID and avatar URL for an existing user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET google_id = ?, avatar_url = ? WHERE user_id = ?",
        (google_id, avatar_url, user_id),
    )
    conn.commit()
    conn.close()


def authenticate_user(email, password):
    """
    Verify credentials and return User or None.
    Demonstrates: conditions, functions.
    """
    user = get_user_by_email(email)
    if user and verify_password(password, user.password_hash):
        return user
    return None


# ─── Candidate CRUD ───────────────────────────────────────────────────────────


def create_candidate(name, position, party, description, photo="default.png"):
    """Insert a new candidate into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO candidates (name, position, party, description, photo) VALUES (?, ?, ?, ?, ?)",
        (name, position, party, description, photo),
    )
    conn.commit()
    conn.close()
    return True


def get_all_candidates():
    """Return a list of all Candidate objects."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY position, name")
    rows = cursor.fetchall()
    conn.close()
    candidates = []
    for row in rows:
        candidates.append(
            Candidate(
                row["candidate_id"],
                row["name"],
                row["position"],
                row["party"],
                row["description"],
                row["photo"],
                row["created_at"],
            )
        )
    return candidates


def get_candidate_by_id(candidate_id):
    """Fetch a single Candidate by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Candidate(
            row["candidate_id"],
            row["name"],
            row["position"],
            row["party"],
            row["description"],
            row["photo"],
            row["created_at"],
        )
    return None


def delete_candidate(candidate_id):
    """Delete a candidate and their associated votes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM votes WHERE candidate_id = ?", (candidate_id,))
    cursor.execute("DELETE FROM candidates WHERE candidate_id = ?", (candidate_id,))
    conn.commit()
    conn.close()


# ─── Voting ───────────────────────────────────────────────────────────────────


def cast_vote(user_id, candidate_id):
    """
    Record a vote.
    Demonstrates: conditions — blocks duplicate votes via UNIQUE constraint.
    Returns: (True, "message") or (False, "error").
    """
    # Check candidate exists
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        return False, "Candidate not found."

    # Check user hasn't already voted
    if has_voted(user_id):
        return False, "You have already cast your vote."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO votes (user_id, candidate_id) VALUES (?, ?)",
            (user_id, candidate_id),
        )
        conn.commit()
        return True, f"Vote cast successfully for {candidate.name}!"
    except sqlite3.IntegrityError:
        return False, "You have already cast your vote."
    finally:
        conn.close()


def has_voted(user_id):
    """Check if a user has already voted."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM votes WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_user_vote(user_id):
    """Return the candidate a user voted for, or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.* FROM votes v
        JOIN candidates c ON v.candidate_id = c.candidate_id
        WHERE v.user_id = ?
    """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return Candidate(
            row["candidate_id"],
            row["name"],
            row["position"],
            row["party"],
            row["description"],
            row["photo"],
            row["created_at"],
        )
    return None


# ─── Results & Statistics ─────────────────────────────────────────────────────


def get_results():
    """
    Aggregate vote counts per candidate.
    Demonstrates: loops, conditions, OOP — returns list of VoteResult objects.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total votes cast
    cursor.execute("SELECT COUNT(*) as total FROM votes")
    total_votes = cursor.fetchone()["total"]

    # Votes per candidate
    cursor.execute("""
        SELECT c.*, COUNT(v.vote_id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.candidate_id = v.candidate_id
        GROUP BY c.candidate_id
        ORDER BY vote_count DESC, c.name
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        candidate = Candidate(
            row["candidate_id"],
            row["name"],
            row["position"],
            row["party"],
            row["description"],
            row["photo"],
            row["created_at"],
        )
        results.append(VoteResult(candidate, row["vote_count"], total_votes))

    return results


def get_statistics():
    """
    Return a dict of overall election statistics.
    Demonstrates: variables, conditions, functions.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = 0")
    total_voters = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM votes")
    total_votes = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM candidates")
    total_candidates = cursor.fetchone()["count"]

    conn.close()

    # Calculate turnout percentage
    turnout = 0.0
    if total_voters > 0:
        turnout = round((total_votes / total_voters) * 100, 2)

    # Voters who haven't voted yet
    pending_voters = total_voters - total_votes

    return {
        "total_voters": total_voters,
        "total_votes": total_votes,
        "total_candidates": total_candidates,
        "turnout": turnout,
        "pending_voters": pending_voters,
    }


def get_recent_votes(limit=10):
    """Return the most recent votes with voter and candidate names."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.name as voter_name, u.student_id, c.name as candidate_name,
               c.position, v.timestamp
        FROM votes v
        JOIN users u ON v.user_id = u.user_id
        JOIN candidates c ON v.candidate_id = c.candidate_id
        ORDER BY v.timestamp DESC
        LIMIT ?
    """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def reset_votes():
    """Delete all votes (admin only). Demonstrates: file handling / data management."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM votes")
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted
