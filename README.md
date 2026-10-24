# Celestius Event Registration API (Python)

A simple REST API built with Python and Flask for the Celestius Backend Team Recruitment Task. Students can register for the **Backend Development Workshop**, and organizers can view registrations.

## Event details

- **Event:** Backend Development Workshop
- **Date:** 24 October 2026
- **Capacity:** 50 participants

## Features

- Register students with a name and email.
- Optionally store college or department.
- Automatically record the registration timestamp.
- Prevent duplicate registrations by email.
- Stop registrations after 50 participants.
- List all registrations and retrieve one by ID.
- View current capacity and remaining seats.
- Validate inputs and return useful HTTP status codes.
- Persist records in an SQLite database.

## Technology

- Python 3.10+
- Flask
- SQLite (included with Python)

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. (Recommended) Create and activate a virtual environment:

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\\Scripts\\activate
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the server:

   ```bash
   python app.py
   ```

6. The API will be available at `http://127.0.0.1:5000`.

The `registrations.db` database and its table are created automatically when the app starts.

## API endpoints

### `POST /register` — register a participant

Send JSON with `Content-Type: application/json`:

```json
{
  "name": "Asha Kumar",
  "email": "asha@example.com",
  "collegeDepartment": "Computer Science"
}
```

`collegeDepartment` is optional. The server generates `registered_at`.

Success response: `201 Created`

```json
{
  "message": "Registration successful.",
  "registration": {
    "id": 1,
    "name": "Asha Kumar",
    "email": "asha@example.com",
    "college_department": "Computer Science",
    "registered_at": "2026-10-23T12:00:00.000+00:00"
  }
}
```

The timestamp is illustrative; the API returns the actual registration time.

Possible errors:
- `400 Bad Request`: missing or invalid fields.
- `409 Conflict`: duplicate email or event full.
- `500 Internal Server Error`: unexpected database/server error.

### `GET /registrations` — view all registrations

Returns the current count, capacity, and all participant records.

### `GET /registrations/<id>` — view one registration

Example: `GET /registrations/1`

- `200 OK`: registration found.
- `404 Not Found`: no registration with that ID.

### `GET /event` — check event capacity

Returns event name, date, capacity, registered count, remaining seats, and whether the event is full.

### `GET /` — API overview

Returns the event details and available endpoint paths.

## Test with curl

Register a participant:

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha Kumar","email":"asha@example.com","collegeDepartment":"Computer Science"}'
```

List registrations:

```bash
curl http://127.0.0.1:5000/registrations
```

View one registration:

```bash
curl http://127.0.0.1:5000/registrations/1
```

Check capacity:

```bash
curl http://127.0.0.1:5000/event
```

You can also test the API using Postman or Thunder Client.

## Design decisions

- **Flask** provides a small, readable way to create HTTP API routes.
- **SQLite** stores records persistently without needing a separate database server.
- **Unique email constraint** prevents duplicate sign-ups, ignoring email capitalization.
- **Server-generated timestamp** prevents clients from choosing their own registration time.
- **Database transaction** checks capacity and inserts a registration together to help avoid overbooking.
- **HTTP status codes** distinguish invalid input, duplicate registration, a full event, and a missing registration.

## Project structure

```text
celestius-event-registration-python/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The SQLite database is created at runtime and is intentionally excluded from Git.

## Scope and limitations

This is a learning/recruitment-task project. It does not include a frontend, organizer login, access control, email notifications, or production deployment. In a production service, access to the participant list should be restricted to authorized organizers.

## Author

Built for the **Celestius Backend Team Recruitment Task**.
