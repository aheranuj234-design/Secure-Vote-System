# E-Voting System

A complete Python Flask-based E-Voting System for college elections, with user registration, login, candidate voting, and live results.

## Run & Operate

- `cd flask-evoting && python app.py` — run the Flask web server (port 5000)
- Default admin: **admin@college.edu** / **admin123**
- Database file: `flask-evoting/evoting.db` (auto-created on first run)

## Stack

- Python 3.12, Flask 3.x
- SQLite (via Python's built-in `sqlite3`)
- HTML5, CSS3 (custom), Vanilla JavaScript
- No external frontend frameworks

## Project Structure

```
flask-evoting/
├── app.py          # Main Flask application — all routes & decorators
├── database.py     # DB layer — SQLite CRUD, stats, vote counting
├── models.py       # OOP classes — User, Candidate, Vote, VoteResult, Election
├── requirements.txt
├── evoting.db      # SQLite database (auto-generated)
├── templates/
│   ├── base.html       # Shared layout with navbar & flash messages
│   ├── index.html      # Landing page with live stats
│   ├── register.html   # Voter registration form
│   ├── login.html      # Login form
│   ├── vote.html       # Candidate cards + confirm modal
│   ├── results.html    # Live results with animated progress bars
│   ├── admin.html      # Admin dashboard (tabs: results/candidates/voters/activity)
│   ├── 404.html
│   └── 500.html
└── static/
    ├── css/style.css   # Full custom CSS with variables, grid, responsive design
    └── js/main.js      # Vanilla JS — animations, toggles, auto-refresh
```

## Features

- User registration with Student ID + email
- Secure login (SHA-256 password hashing)
- One-vote-per-user enforcement (DB UNIQUE constraint)
- Candidate cards grouped by position
- Confirm-before-submit vote modal
- Live results page with animated progress bars (auto-refreshes every 30s)
- Admin dashboard: live tally, candidate management, voter list, recent activity, vote reset
- Sample candidates seeded automatically

## Python Concepts Demonstrated

- **OOP classes**: `User`, `Candidate`, `Vote`, `VoteResult`, `Election` (models.py)
- **Functions**: all DB operations, route handlers, decorators
- **Loops**: iterating candidates, building grouped positions, seeding data
- **Conditions**: form validation, auth checks, duplicate vote prevention
- **File handling**: SQLite `.db` file created and managed at runtime
- **Variables**: election metadata, stats dictionaries, session data

## pnpm Workspace

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM (workspace API server — separate from Flask app)

## User preferences

- Project is a Python Flask standalone app inside `flask-evoting/` directory
- Run with `python app.py` from inside `flask-evoting/`
