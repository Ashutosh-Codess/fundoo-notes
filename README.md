# Fundoo Notes

A notes API built with FastAPI and MySQL. A user owns many notes, and notes share a many-to-many relationship with labels. Includes JWT authentication and an async CSV export of a user's data.

## Data model

- User has many Notes (one to many)
- Notes have many Labels and Labels belong to many Notes (many to many)

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your MySQL credentials and a JWT secret.

```powershell
copy .env.example .env
```

The database and tables are created automatically on startup, so you only need MySQL running.

## Run

```powershell
uvicorn app.main:app --reload
```

Open the interactive docs at http://127.0.0.1:8000/docs

## Auth flow

1. `POST /users/register` with name, email, password
2. `POST /users/login` to receive an access token
3. Send the token as `Authorization: Bearer <token>` on every protected route

## Endpoints

Users
- `POST /users/register`
- `POST /users/login`
- `GET /users/me`

Notes
- `POST /notes`
- `GET /notes`
- `GET /notes/{note_id}`
- `PUT /notes/{note_id}`
- `DELETE /notes/{note_id}`
- `GET /notes/{note_id}/labels`
- `POST /notes/{note_id}/labels/{label_id}`
- `DELETE /notes/{note_id}/labels/{label_id}`

Labels
- `POST /labels`
- `GET /labels`
- `DELETE /labels/{label_id}`

Export
- `POST /notes/export`

```json
{
  "user_id": 1,
  "filenames": ["notes.csv", "labels.csv", "mappings.csv"]
}
```

Files are written concurrently with asyncio into `data/user{id}/`.
