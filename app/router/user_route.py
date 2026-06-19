from fastapi import APIRouter, HTTPException, status, Depends
import mysql.connector

from app.schemas.user_schema import UserRegister, UserLogin, UserResponse, TokenResponse
from app.config.database import get_connection
from app.config.logger import get_logger
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger("user_route")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (payload.name, payload.email, hash_password(payload.password)),
        )
        connection.commit()
        user_id = cursor.lastrowid
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    finally:
        cursor.close()
        connection.close()

    logger.info("Registered user %s", payload.email)
    return {"id": user_id, "name": payload.name, "email": payload.email}


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (payload.email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_profile(user_id: int = Depends(get_current_user)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
