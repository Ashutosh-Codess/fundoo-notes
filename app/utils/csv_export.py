import os
import csv
import asyncio

from app.config.database import get_connection
from app.config.logger import get_logger

logger = get_logger("csv_export")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def fetch_user_data(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, title, description, color, is_archived, is_pinned, created_at "
        "FROM notes WHERE user_id = %s",
        (user_id,),
    )
    notes = cursor.fetchall()

    cursor.execute(
        "SELECT id, name, created_at FROM labels WHERE user_id = %s",
        (user_id,),
    )
    labels = cursor.fetchall()

    cursor.execute(
        "SELECT nl.note_id, nl.label_id FROM note_labels nl "
        "JOIN notes n ON n.id = nl.note_id WHERE n.user_id = %s",
        (user_id,),
    )
    mappings = cursor.fetchall()

    cursor.close()
    connection.close()
    return notes, labels, mappings


async def write_csv(path, rows, headers):
    def _write():
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    await asyncio.to_thread(_write)
    logger.info("Exported %s rows to %s", len(rows), path)


async def export_user_data(user_id, filenames):
    notes, labels, mappings = fetch_user_data(user_id)

    user_dir = os.path.join(DATA_DIR, f"user{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    datasets = [
        (notes, ["id", "title", "description", "color", "is_archived", "is_pinned", "created_at"]),
        (labels, ["id", "name", "created_at"]),
        (mappings, ["note_id", "label_id"]),
    ]

    tasks = []
    for filename, (rows, headers) in zip(filenames, datasets):
        path = os.path.join(user_dir, filename)
        tasks.append(write_csv(path, rows, headers))

    await asyncio.gather(*tasks)
    return [os.path.join(f"user{user_id}", name) for name in filenames]
