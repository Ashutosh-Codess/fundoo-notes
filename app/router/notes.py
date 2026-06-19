from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.notes import NoteCreate, NoteUpdate, NoteResponse, ExportRequest
from app.schemas.labels import LabelResponse
from app.config.database import get_connection
from app.config.logger import get_logger
from app.utils.dependencies import get_current_user
from app.utils.csv_export import export_user_data

router = APIRouter(prefix="/notes", tags=["Notes"])
logger = get_logger("notes")

NOTE_COLUMNS = "id, title, description, color, is_archived, is_pinned, user_id"


def get_owned_note(note_id, user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        f"SELECT {NOTE_COLUMNS} FROM notes WHERE id = %s AND user_id = %s",
        (note_id, user_id),
    )
    note = cursor.fetchone()
    cursor.close()
    connection.close()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


def get_owned_label(label_id, user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, user_id FROM labels WHERE id = %s AND user_id = %s",
        (label_id, user_id),
    )
    label = cursor.fetchone()
    cursor.close()
    connection.close()
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")
    return label


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, user_id: int = Depends(get_current_user)):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO notes (title, description, color, is_archived, is_pinned, user_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (payload.title, payload.description, payload.color, payload.is_archived, payload.is_pinned, user_id),
    )
    connection.commit()
    note_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return get_owned_note(note_id, user_id)


@router.get("", response_model=List[NoteResponse])
def list_notes(user_id: int = Depends(get_current_user)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT {NOTE_COLUMNS} FROM notes WHERE user_id = %s", (user_id,))
    notes = cursor.fetchall()
    cursor.close()
    connection.close()
    return notes


@router.post("/export")
async def export_notes(payload: ExportRequest, user_id: int = Depends(get_current_user)):
    if payload.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot export another user's data")
    if len(payload.filenames) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide three filenames for notes, labels and mappings",
        )
    files = await export_user_data(payload.user_id, payload.filenames)
    return {"message": "Export complete", "files": files}


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, user_id: int = Depends(get_current_user)):
    return get_owned_note(note_id, user_id)


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, payload: NoteUpdate, user_id: int = Depends(get_current_user)):
    get_owned_note(note_id, user_id)
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    assignments = ", ".join(f"{column} = %s" for column in fields)
    values = list(fields.values())
    values.append(note_id)

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE notes SET {assignments} WHERE id = %s", values)
    connection.commit()
    cursor.close()
    connection.close()
    return get_owned_note(note_id, user_id)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, user_id: int = Depends(get_current_user)):
    get_owned_note(note_id, user_id)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    connection.commit()
    cursor.close()
    connection.close()


@router.get("/{note_id}/labels", response_model=List[LabelResponse])
def list_note_labels(note_id: int, user_id: int = Depends(get_current_user)):
    get_owned_note(note_id, user_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT l.id, l.name, l.user_id FROM labels l "
        "JOIN note_labels nl ON nl.label_id = l.id WHERE nl.note_id = %s",
        (note_id,),
    )
    labels = cursor.fetchall()
    cursor.close()
    connection.close()
    return labels


@router.post("/{note_id}/labels/{label_id}", status_code=status.HTTP_200_OK)
def attach_label(note_id: int, label_id: int, user_id: int = Depends(get_current_user)):
    get_owned_note(note_id, user_id)
    get_owned_label(label_id, user_id)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT IGNORE INTO note_labels (note_id, label_id) VALUES (%s, %s)",
        (note_id, label_id),
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Label attached"}


@router.delete("/{note_id}/labels/{label_id}", status_code=status.HTTP_200_OK)
def detach_label(note_id: int, label_id: int, user_id: int = Depends(get_current_user)):
    get_owned_note(note_id, user_id)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM note_labels WHERE note_id = %s AND label_id = %s",
        (note_id, label_id),
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Label detached"}
