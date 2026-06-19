from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
import mysql.connector

from app.schemas.labels import LabelCreate, LabelResponse
from app.config.database import get_connection
from app.config.logger import get_logger
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/labels", tags=["Labels"])
logger = get_logger("labels")


@router.post("", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(payload: LabelCreate, user_id: int = Depends(get_current_user)):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO labels (name, user_id) VALUES (%s, %s)",
            (payload.name, user_id),
        )
        connection.commit()
        label_id = cursor.lastrowid
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Label already exists")
    finally:
        cursor.close()
        connection.close()
    return {"id": label_id, "name": payload.name, "user_id": user_id}


@router.get("", response_model=List[LabelResponse])
def list_labels(user_id: int = Depends(get_current_user)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, name, user_id FROM labels WHERE user_id = %s", (user_id,))
    labels = cursor.fetchall()
    cursor.close()
    connection.close()
    return labels


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(label_id: int, user_id: int = Depends(get_current_user)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id FROM labels WHERE id = %s AND user_id = %s", (label_id, user_id))
    label = cursor.fetchone()
    if not label:
        cursor.close()
        connection.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")
    cursor.execute("DELETE FROM labels WHERE id = %s", (label_id,))
    connection.commit()
    cursor.close()
    connection.close()
