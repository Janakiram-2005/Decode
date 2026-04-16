from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.database import get_database
from app.models import UserCreate, UserLogin, UserResponse, Token, TokenData
from app.utils.security import verify_password, get_password_hash, create_access_token, ALGORITHM, SECRET_KEY
from jose import JWTError, jwt
from typing import Annotated
import uuid
from datetime import datetime, timedelta
import os

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    db = get_database()
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    
    # Determine Role
    # Determine Role
    role = "user"
    if user.admin_secret:
        # Check both possible env var names for compatibility
        admin_secret_env = os.getenv("ADMIN_REGISTER_SECRET") or os.getenv("ADMIN_REGISTER")
        
        if admin_secret_env and user.admin_secret == admin_secret_env:
            role = "admin"
        else:
            # Strict check: If user attempts to be admin but fails secret, DENY registration.
            # This prevents accidental "User" creation when "Admin" was intended.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Admin Secret Key"
            )
    
    user_dict = {
        "user_id": str(uuid.uuid4()),
        "email": user.email,
        "password_hash": hashed_password,
        "role": role,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_dict)
    return user_dict

@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    db = get_database()
    user = await db.users.find_one({"email": form_data.username})
    if not user:
        print(f"Login failed: User {form_data.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user['password_hash']):
        print(f"Login failed: Password mismatch for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": user["email"], "role": user.get("role", "user")}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.get("role", "user")
    }
