from datetime import datetime, timezone
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "registrations.db"
EVENT_NAME = "Backend Development Workshop"
EVENT_DATE = "2026-10-20"
EVENT_CAPACITY = 50


def get_db():
    """Open one SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """Close the request's database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the registrations table if it does not exist yet."""
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                college_department TEXT,
                registered_at TEXT NOT NULL
            )
        """)
        db.commit()


def registration_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "college_department": row["college_department"],
        "registered_at": row["registered_at"],
    }


@app.get("/")
def home():
    return jsonify({
        "message": "Celestius Event Registration API",
        "event": {
            "name": EVENT_NAME,
            "date": EVENT_DATE,
            "capacity": EVENT_CAPACITY,
        },
        "endpoints": {
            "register": "POST /register",
            "list": "GET /registrations",
            "single": "GET /registrations/<id>",
            "event_status": "GET /event",
        },
    })


@app.get("/event")
def event_status():
    db = get_db()
    registered = db.execute(
        "SELECT COUNT(*) FROM registrations"
    ).fetchone()[0]

    return jsonify({
        "event": EVENT_NAME,
        "date": EVENT_DATE,
        "capacity": EVENT_CAPACITY,
        "registered": registered,
        "seatsRemaining": max(EVENT_CAPACITY - registered, 0),
        "isFull": registered >= EVENT_CAPACITY,
    })


@app.post("/register")
def register():
    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    name = body.get("name")
    email = body.get("email")
    college_department = body.get("collegeDepartment")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Name is required."}), 400

    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Email is required."}), 400

    name = name.strip()
    email = email.strip().lower()

    if len(name) > 100:
        return jsonify({"error": "Name must be 100 characters or fewer."}), 400

    if len(email) > 254 or not re.fullmatch(r"[^\\s@]+@[^\\s@]+\\.[^\\s@]+", email):
        return jsonify({"error": "Please provide a valid email address."}), 400

    if college_department is not None and not isinstance(college_department, str):
        return jsonify({
            "error": "collegeDepartment must be a string when provided."
        }), 400

    if isinstance(college_department, str):
        college_department = college_department.strip() or None
        if college_department and len(college_department) > 150:
            return jsonify({
                "error": "College/department must be 150 characters or fewer."
            }), 400

    db = get_db()

    # Check for duplicates before checking capacity for a clearer response.
    existing = db.execute(
        "SELECT id FROM registrations WHERE email = ?", (email,)
    ).fetchone()
    if existing:
        return jsonify({
            "error": "This email is already registered for the event."
        }), 409

    # BEGIN IMMEDIATE obtains a write lock before checking capacity, so two
    # requests cannot both take the final seat.
    try:
        db.execute("BEGIN IMMEDIATE")
        count = db.execute(
            "SELECT COUNT(*) FROM registrations"
        ).fetchone()[0]

        if count >= EVENT_CAPACITY:
            db.rollback()
            return jsonify({"error": "Event is full."}), 409

        registered_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        cursor = db.execute("""
            INSERT INTO registrations
                (name, email, college_department, registered_at)
            VALUES (?, ?, ?, ?)
        """, (name, email, college_department, registered_at))

        registration_id = cursor.lastrowid
        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "This email is already registered for the event."
        }), 409
    except sqlite3.Error:
        db.rollback()
        app.logger.exception("Database error while registering participant")
        return jsonify({"error": "Internal server error."}), 500

    row = db.execute(
        """SELECT id, name, email, college_department, registered_at
           FROM registrations WHERE id = ?""",
        (registration_id,),
    ).fetchone()

    return jsonify({
        "message": "Registration successful.",
        "registration": registration_to_dict(row),
    }), 201


@app.get("/registrations")
def list_registrations():
    db = get_db()
    rows = db.execute("""
        SELECT id, name, email, college_department, registered_at
        FROM registrations
        ORDER BY registered_at ASC, id ASC
    """).fetchall()

    return jsonify({
        "count": len(rows),
        "capacity": EVENT_CAPACITY,
        "registrations": [registration_to_dict(row) for row in rows],
    })


@app.get("/registrations/<int:registration_id>")
def get_registration(registration_id):
    row = get_db().execute("""
        SELECT id, name, email, college_department, registered_at
        FROM registrations WHERE id = ?
    """, (registration_id,)).fetchone()

    if row is None:
        return jsonify({"error": "Registration not found."}), 404

    return jsonify({"registration": registration_to_dict(row)})


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route not found."}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed for this route."}), 405


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
