"""
app.py - Main Flask Application: E-Voting System
Run with: python app.py

Demonstrates: variables, loops, conditions, functions, OOP, file handling
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import os
import urllib.parse
import hashlib
import secrets

import database as db
from models import Election

# ─── App Configuration ────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.environ.get("SECRET_KEY", "evoting-secret-key-2024"))

# Trust the Replit reverse proxy so request.url / url_for use https://
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Election metadata (variables)
ELECTION_NAME = "Student Union Election 2026"
ELECTION_DESCRIPTION = "Vote for your student representatives"
COLLEGE_NAME = "Nutan Maharashtra Institute of Engineering And Technology"


# ─── Decorators (Higher-order functions) ─────────────────────────────────────

def login_required(f):
    """Decorator: redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: restrict route to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


# ─── Context Processor ───────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    return {
        "election_name":    ELECTION_NAME,
        "college_name":     COLLEGE_NAME,
        "current_user_id":  session.get("user_id"),
        "current_user_name": session.get("user_name"),
        "current_avatar":   session.get("avatar_url", ""),
        "is_admin":         session.get("is_admin", False),
    }


# ─── Routes: Public ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Landing / Home page."""
    stats = db.get_statistics()
    return render_template("index.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration.
    Demonstrates: conditions, functions, POST form handling.
    """
    if "user_id" in session:
        return redirect(url_for("vote"))

    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        email      = request.form.get("email", "").strip().lower()
        password   = request.form.get("password", "")
        confirm    = request.form.get("confirm_password", "")
        student_id = request.form.get("student_id", "").strip().upper()

        # Validation conditions
        errors = []
        if not name:
            errors.append("Full name is required.")
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if not student_id:
            errors.append("Student ID is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html",
                                   name=name, email=email, student_id=student_id)

        # Attempt to create user
        success = db.create_user(name, email, password, student_id)
        if success:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Email or Student ID already registered. Please log in.", "danger")
            return render_template("register.html",
                                   name=name, email=email, student_id=student_id)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User login.
    Demonstrates: conditions, session management.
    """
    if "user_id" in session:
        return redirect(url_for("vote"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Both email and password are required.", "danger")
            return render_template("login.html", email=email)

        user = db.authenticate_user(email, password)
        if user:
            # Store user info in session
            session["user_id"]   = user.user_id
            session["user_name"] = user.name
            session["is_admin"]  = user.is_admin
            flash(f"Welcome back, {user.name}!", "success")

            # Redirect admin to dashboard
            if user.is_admin:
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("vote"))
        else:
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and redirect to home."""
    user_name = session.get("user_name", "User")
    session.clear()
    flash(f"Goodbye, {user_name}! You have been logged out.", "info")
    return redirect(url_for("index"))


# ─── Routes: Voting ──────────────────────────────────────────────────────────

@app.route("/vote")
@login_required
def vote():
    """
    Voting page — shows candidate cards.
    Demonstrates: loops (candidates), conditions (already voted).
    """
    user_id    = session["user_id"]
    voted      = db.has_voted(user_id)
    voted_for  = db.get_user_vote(user_id) if voted else None
    candidates = db.get_all_candidates()

    # Group candidates by position using a loop
    positions = {}
    for candidate in candidates:
        position = candidate.position
        if position not in positions:
            positions[position] = []
        positions[position].append(candidate)

    return render_template("vote.html",
                           candidates=candidates,
                           positions=positions,
                           voted=voted,
                           voted_for=voted_for)


@app.route("/cast_vote", methods=["POST"])
@login_required
def cast_vote():
    """
    Handle vote submission.
    Demonstrates: conditions, functions, POST handling.
    """
    user_id      = session["user_id"]
    candidate_id = request.form.get("candidate_id")

    if not candidate_id:
        flash("No candidate selected. Please choose a candidate.", "warning")
        return redirect(url_for("vote"))

    # Validate candidate_id is a valid integer
    try:
        candidate_id = int(candidate_id)
    except (ValueError, TypeError):
        flash("Invalid candidate selection.", "danger")
        return redirect(url_for("vote"))

    success, message = db.cast_vote(user_id, candidate_id)

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("vote"))


# ─── Routes: Results ─────────────────────────────────────────────────────────

@app.route("/results")
def results():
    """
    Public results page.
    Demonstrates: loops (results), VoteResult objects.
    """
    results_list = db.get_results()
    stats        = db.get_statistics()

    # Find winners per position using a loop
    winners = {}
    for result in results_list:
        pos = result.candidate.position
        if pos not in winners or result.vote_count > winners[pos].vote_count:
            winners[pos] = result

    return render_template("results.html",
                           results=results_list,
                           stats=stats,
                           winners=winners)


@app.route("/api/results")
def api_results():
    """JSON endpoint for live results — consumed by JavaScript."""
    results_list = db.get_results()
    stats        = db.get_statistics()
    data = {
        "stats": stats,
        "results": [r.to_dict() for r in results_list],
    }
    return jsonify(data)


# ─── Routes: Admin Dashboard ─────────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_dashboard():
    """
    Admin dashboard — overview of election status.
    Demonstrates: functions, loops, conditions.
    """
    stats         = db.get_statistics()
    candidates    = db.get_all_candidates()
    users         = db.get_all_users()
    recent_votes  = db.get_recent_votes(limit=10)
    results_list  = db.get_results()

    return render_template("admin.html",
                           stats=stats,
                           candidates=candidates,
                           users=users,
                           recent_votes=recent_votes,
                           results=results_list)


@app.route("/admin/add_candidate", methods=["POST"])
@admin_required
def add_candidate():
    """Add a new candidate from the admin dashboard."""
    name        = request.form.get("name", "").strip()
    position    = request.form.get("position", "").strip()
    party       = request.form.get("party", "").strip()
    description = request.form.get("description", "").strip()

    errors = []
    if not name:
        errors.append("Candidate name is required.")
    if not position:
        errors.append("Position is required.")
    if not party:
        errors.append("Party/group name is required.")

    if errors:
        for e in errors:
            flash(e, "danger")
    else:
        db.create_candidate(name, position, party, description)
        flash(f"Candidate '{name}' added successfully.", "success")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete_candidate/<int:candidate_id>", methods=["POST"])
@admin_required
def delete_candidate(candidate_id):
    """Delete a candidate and all their votes."""
    candidate = db.get_candidate_by_id(candidate_id)
    if candidate:
        db.delete_candidate(candidate_id)
        flash(f"Candidate '{candidate.name}' has been removed.", "info")
    else:
        flash("Candidate not found.", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reset_votes", methods=["POST"])
@admin_required
def reset_votes():
    """Reset (delete) all votes — admin only."""
    deleted = db.reset_votes()
    flash(f"All votes have been reset. ({deleted} votes removed)", "warning")
    return redirect(url_for("admin_dashboard"))


# ─── Google OAuth ─────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_AUTH_URL      = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL     = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"

# Allow OAuth over HTTP in dev (Replit dev URLs use HTTPS via proxy, but
# the internal callback may be plain HTTP — this env flag handles that)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def _google_callback_url():
    """
    Build the correct public callback URL for Google OAuth.
    Uses REPLIT_DOMAINS when running on Replit so the URL is
    externally reachable (not localhost:5000).
    """
    replit_domain = os.environ.get("REPLIT_DOMAINS", "").split(",")[0].strip()
    if replit_domain:
        return f"https://{replit_domain}/auth/google/callback"
    # Local dev fallback
    return url_for("google_callback", _external=True)


def _login_user(user, avatar_url=""):
    """Store user info in session and redirect appropriately."""
    session["user_id"]    = user.user_id
    session["user_name"]  = user.name
    session["user_email"] = user.email
    session["is_admin"]   = user.is_admin
    session["avatar_url"] = avatar_url or user.avatar_url or ""
    if user.is_admin:
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("vote"))


@app.route("/auth/google")
def google_login():
    """Show the Google-styled sign-in form (demo flow)."""
    if "user_id" in session:
        return redirect(url_for("vote"))
    return render_template("google_login.html", error=None)


@app.route("/auth/google/callback")
def google_callback():
    """Handle the real Google OAuth callback."""
    from authlib.integrations.requests_client import OAuth2Session

    if not GOOGLE_CLIENT_ID:
        flash("Google login is not configured.", "warning")
        return redirect(url_for("login"))

    callback_url = _google_callback_url()
    oauth = OAuth2Session(
        GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=callback_url,
        state=session.pop("oauth_state", ""),
    )

    # Ensure the authorization_response URL uses https:// even if the
    # internal Flask request came in over plain HTTP (Replit proxy strips TLS).
    auth_response = request.url
    if auth_response.startswith("http://"):
        auth_response = "https://" + auth_response[7:]

    try:
        oauth.fetch_token(
            GOOGLE_TOKEN_URL,
            authorization_response=auth_response,
            client_secret=GOOGLE_CLIENT_SECRET,
        )
    except Exception as exc:
        app.logger.error("Google token exchange failed: %s", exc)
        flash("Google authentication failed. Please try again.", "danger")
        return redirect(url_for("login"))

    try:
        user_info = oauth.get(GOOGLE_USERINFO_URL).json()
    except Exception:
        flash("Could not retrieve your Google profile.", "danger")
        return redirect(url_for("login"))

    google_email = user_info.get("email", "").lower().strip()
    google_name  = user_info.get("name", "Google User")
    google_id    = user_info.get("sub", "")
    avatar_url   = user_info.get("picture", "")

    if not google_email:
        flash("No email returned from Google.", "danger")
        return redirect(url_for("login"))

    user = db.get_user_by_email(google_email)
    if not user:
        student_id = f"G-{hashlib.md5(google_id.encode()).hexdigest()[:8].upper()}"
        db.create_google_user(google_name, google_email, google_id, avatar_url, student_id)
        user = db.get_user_by_email(google_email)
        flash(f"Welcome, {google_name}! Your account has been created.", "success")
    else:
        db.update_google_user(user.user_id, google_id, avatar_url)
        user = db.get_user_by_id(user.user_id)
        flash(f"Welcome back, {user.name}!", "success")

    if user:
        return _login_user(user, avatar_url)

    flash("Login failed. Please try again.", "danger")
    return redirect(url_for("login"))


@app.route("/auth/google/demo", methods=["GET", "POST"])
def google_login_demo():
    """
    Demo Google sign-in (used when real credentials are not configured).
    GET  — show the Google-styled demo form.
    POST — process submitted email and log the user in.
    """
    if "user_id" in session:
        return redirect(url_for("vote"))

    if request.method == "GET":
        return render_template("google_login.html", error=None)

    google_email = request.form.get("google_email", "").strip().lower()
    google_name  = request.form.get("google_name", "").strip()

    if not google_email or "@" not in google_email:
        return render_template("google_login.html", error="Enter a valid email address.")

    if not google_name:
        google_name = google_email.split("@")[0].replace(".", " ").replace("_", " ").title()

    user = db.get_user_by_email(google_email)
    if not user:
        student_id = f"G-{hashlib.md5(google_email.encode()).hexdigest()[:8].upper()}"
        db.create_google_user(google_name, google_email, "", "", student_id)
        user = db.get_user_by_email(google_email)
        flash(f"Welcome, {google_name}! Account created via Google.", "success")
    else:
        flash(f"Welcome back, {user.name}!", "success")

    if user:
        return _login_user(user)

    flash("Something went wrong. Please try again.", "danger")
    return redirect(url_for("login"))


# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Initialise database (file handling — creates evoting.db)
    print("=" * 50)
    print(f"  {COLLEGE_NAME}")
    print(f"  {ELECTION_NAME}")
    print("=" * 50)
    print("Initialising database...")
    db.init_db()
    print("Database ready.")
    print("\nDefault admin credentials:")
    print("  Email   : admin@college.edu")
    print("  Password: admin123")
    print("\nStarting server at http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
