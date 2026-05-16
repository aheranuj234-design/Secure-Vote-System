"""
models.py - OOP Classes for E-Voting System
Demonstrates: OOP, classes, methods, properties
"""

from datetime import datetime


class User:
    """Represents a registered voter in the system."""

    def __init__(self, user_id, name, email, password_hash, student_id,
                 is_admin=False, created_at=None, google_id=None, avatar_url=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.student_id = student_id
        self.is_admin = bool(is_admin)
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.google_id = google_id or ""
        self.avatar_url = avatar_url or ""

    @property
    def is_google_user(self):
        """Return True if this account was created via Google OAuth."""
        return bool(self.google_id)

    @property
    def display_avatar(self):
        """Return avatar URL or empty string if none."""
        return self.avatar_url or ""

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            "user_id":    self.user_id,
            "name":       self.name,
            "email":      self.email,
            "student_id": self.student_id,
            "is_admin":   self.is_admin,
            "created_at": self.created_at,
            "avatar_url": self.avatar_url,
            "is_google":  self.is_google_user,
        }

    def __repr__(self):
        return f"User(id={self.user_id}, name={self.name}, email={self.email})"


class Candidate:
    """Represents a candidate in the election."""

    # Class variable to track all candidates
    candidate_count = 0

    def __init__(self, candidate_id, name, position, party, description, photo=None, created_at=None):
        self.candidate_id = candidate_id
        self.name = name
        self.position = position
        self.party = party
        self.description = description
        self.photo = photo or "default.png"
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        Candidate.candidate_count += 1

    def get_initials(self):
        """Return initials from candidate name."""
        parts = self.name.strip().split()
        initials = ""
        for part in parts:
            if part:
                initials += part[0].upper()
        return initials[:2]

    def to_dict(self):
        """Convert candidate object to dictionary."""
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "position": self.position,
            "party": self.party,
            "description": self.description,
            "photo": self.photo,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return f"Candidate(id={self.candidate_id}, name={self.name}, position={self.position})"


class Vote:
    """Represents a single vote cast by a user."""

    def __init__(self, vote_id, user_id, candidate_id, timestamp=None):
        self.vote_id = vote_id
        self.user_id = user_id
        self.candidate_id = candidate_id
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Convert vote object to dictionary."""
        return {
            "vote_id": self.vote_id,
            "user_id": self.user_id,
            "candidate_id": self.candidate_id,
            "timestamp": self.timestamp,
        }

    def __repr__(self):
        return f"Vote(id={self.vote_id}, user_id={self.user_id}, candidate_id={self.candidate_id})"


class VoteResult:
    """Represents aggregated results for a candidate."""

    def __init__(self, candidate, vote_count, total_votes):
        self.candidate = candidate
        self.vote_count = vote_count
        self.total_votes = total_votes

    @property
    def percentage(self):
        """Calculate percentage of votes received."""
        if self.total_votes == 0:
            return 0.0
        return round((self.vote_count / self.total_votes) * 100, 2)

    def to_dict(self):
        """Convert result object to dictionary."""
        result = self.candidate.to_dict()
        result["vote_count"] = self.vote_count
        result["percentage"] = self.percentage
        result["total_votes"] = self.total_votes
        return result

    def __repr__(self):
        return f"VoteResult(candidate={self.candidate.name}, votes={self.vote_count}, pct={self.percentage}%)"


class Election:
    """Represents an election with candidates and results."""

    def __init__(self, name, description, is_active=True):
        self.name = name
        self.description = description
        self.is_active = is_active
        self.candidates = []
        self.votes = []

    def add_candidate(self, candidate):
        """Add a candidate to the election."""
        self.candidates.append(candidate)

    def get_total_votes(self):
        """Return total number of votes cast."""
        return len(self.votes)

    def get_winner(self, results):
        """Determine the winner from results list."""
        if not results:
            return None
        winner = results[0]
        for result in results:
            if result.vote_count > winner.vote_count:
                winner = result
        return winner

    def __repr__(self):
        return f"Election(name={self.name}, candidates={len(self.candidates)}, active={self.is_active})"
