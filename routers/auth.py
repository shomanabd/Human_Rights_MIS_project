from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from datetime import timedelta
from models.user import User, UserRole
from security.auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from db import users_collection

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBasic()

@router.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    """Login and receive JWT token"""
    user = users_collection.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}