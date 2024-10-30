from functools import wraps
from typing import Annotated, Optional
from datetime import datetime, timedelta
import jwt

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

import db_models
from database import SessionLocal
from models.login_model import login_data, detailing, DataSetOut
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

SECRET_KEY = os.getenv("secret_key")  # Change this to a strong secret key
ALGORITHM = os.getenv("algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("access_token_expiry"))

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# JWT utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def check_authentication(db: Session, creds: login_data):
    admin_creds = db.query(db_models.admin).filter(db_models.admin.username == creds.username).first()
    if admin_creds is None or not check_password_hash(admin_creds.password, creds.password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return admin_creds

def requires_authentication():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get('token')
            if token is None or verify_token(token) is None:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/")
async def home():
    return {"reached": "home"}

@app.post("/add_admin")
async def admin_addition(data: login_data, db: db_dependency):
    try:
        hashed_password = generate_password_hash(data.password)
        data.password = hashed_password
        db_admin = db_models.admin(**data.dict())
        db.add(db_admin)
        db.commit()
        return {status.HTTP_200_OK: f"{data.username} created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# from sqlalchemy.orm import Session
# from sqlalchemy import update


@app.post("/auth")
async def login(creds: login_data, db: db_dependency):
    # Authenticate the user
    admin_creds = check_authentication(db, creds)

    if admin_creds:
        access_token = create_access_token(data={"sub": admin_creds.username})

        # Update the existing token and expiry in the database
        try:
            db.query(db_models.admin).filter(db_models.admin.username == admin_creds.username).update(
                {
                    db_models.admin.token: access_token,
                    db_models.admin.expiry: datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                }
            )
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return DataSetOut(status_code=200, details="Login successful", token=access_token)

    raise HTTPException(status_code=403, detail="Wrong password")

@app.post("/details")
@requires_authentication()
async def upload_details(creds: login_data, required_detail: detailing, token: str, db: db_dependency):
    db_details = db_models.CompanyDetails(**required_detail.dict())
    db.add(db_details)
    db.commit()

    data = {
        "company": required_detail.company,
        "designation": required_detail.designation,
        "description": required_detail.description,
        "file_path": required_detail.image
    }
    return DataSetOut(status_code=200, details=data)

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    uvicorn.run(app="main2:app", host="0.0.0.0", port=5000, reload=True)