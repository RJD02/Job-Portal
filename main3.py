from functools import wraps
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

import db_models
from database import SessionLocal
from models.login_model import login_data, detailing, DataSetOut

app = FastAPI()

# Assuming SessionLocal, db_models, login_data, and detailing are already defined

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]


def check_authentication(db: Session, creds: login_data):
    admin_creds = db.query(db_models.admin).filter(db_models.admin.username == creds.username).first()
    if admin_creds is None or not check_password_hash(admin_creds.password, creds.password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def requires_authentication():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = next(get_db())
            creds = kwargs.get('data') or kwargs.get('creds')
            if creds is None:
                raise HTTPException(status_code=401, detail="Unauthorized")
            check_authentication(db, creds)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/")
async def home():
    return {"reached": "home"}

@app.post("/add_admin")
@requires_authentication()
async def admin_addition(data: login_data, db: db_dependency):
    try:
        password = check_password_hash(data.password)
        data.password = password
        db_admin = db_models.admin(**data.dict())
        db.add(db_admin)
        db.commit()
        return {status.HTTP_200_OK: f"{data.username} created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

@app.post("/auth")
async def login(creds: login_data, db: db_dependency):
    admin_creds = db.query(db_models.admin).filter(db_models.admin.username == creds.username).first()
    if admin_creds is None:
        raise HTTPException(status_code=404, detail="User not found")
    elif check_password_hash(admin_creds.password, creds.password):
        return DataSetOut(status_code=200,details = "Login")
        return {status.HTTP_200_OK: "Login"}
    else:
        raise HTTPException(status_code=403, detail="Wrong password")

@app.post("/details")
@requires_authentication()
async def upload_details(creds: login_data,required_detail: detailing,db: db_dependency):
    db_details = db_models.CompanyDetails(**required_detail.dict())
    db.add(db_details)
    db.commit()

    data = {
        "company": required_detail.company,
        "designation": required_detail.designation,
        "description": required_detail.description,
        "file_path": required_detail.image
    }
    return DataSetOut(status_code=200,details = data)


    # return {status.HTTP_200_OK: data}