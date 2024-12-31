from functools import wraps
from typing import Annotated, Optional
from datetime import datetime, timedelta, date
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

#isactive or inactive function
def is_active(company: db_models.CompanyDetails) -> bool:
    # If inactive_date is None or it is in the future, it's still active
    if company.inactive_date is None or company.inactive_date >= date.today():
        return True
    return False

@app.post("/")
async def home(db: Session = Depends(get_db)):
    # Query all company details from the database
    company_details = db.query(db_models.CompanyDetails).all()

    # Filter active companies using the is_active function
    active_companies = [company for company in company_details if is_active(company)]

    # Convert the active result into a list of dictionaries (or any other serializable format)
    result = [{"id": company.id, "company": company.company, "designation": company.designation,
               "description": company.description, "image": company.image,"application": company.application} for company in active_companies]

    return {"company_details": result}
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


@app.put("/update/{company_id}")
@requires_authentication()
async def update_details(company_id: int, token: str,company_data: detailing, db: Session = Depends(get_db)):
    try:
            # Get the company record by ID
            company = db.query(db_models.CompanyDetails).filter(db_models.CompanyDetails.id == company_id).first()
            # print("company")
            print(company)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            # Update fields from company_data (no need to manually extract them)
            # inactive_date = required_detail.inactive_date or (date.today() + timedelta(days=10))
            company.company = company_data.company
            company.designation = company_data.designation
            company.description = company_data.description
            company.image = company_data.image
            company.updated_date = company_data.updated_date
            company.inactive_date = company_data.inactive_date or (date.today() + timedelta(days=10))
            company.application = company_data.application
            company.salary = company_data.salary or ("NA")
            company.batch = company_data.batch

            # Commit the changes
            db.commit()

            data = {
                "company": company_data.company,
                "designation": company_data.designation,
                "description": company_data.description,
                "file_path": company_data.image,
                "update_date": company_data.updated_date,
                "inactive_data": company.inactive_date,
                "application": company_data.application,
                "salary": company.salary,
                "batch": company_data.batch

            }

            # Return the updated company details as response
            return DataSetOut(status_code=200,details=data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/details")
@requires_authentication()
async def upload_details(required_detail: detailing, db: db_dependency,token: str):
    try:
        inactive_date = required_detail.inactive_date or (date.today() + timedelta(days=10))
        salary = required_detail.salary or ("NA")
        # Create the db model object
        required_detail.inactive_date = inactive_date
        db_details = db_models.CompanyDetails(**required_detail.dict())

        # Add to the database
        db.add(db_details)
        db.commit()

        # Prepare the response data
        data = {
            "company": required_detail.company,
            "designation": required_detail.designation,
            "description": required_detail.description,
            "file_path": required_detail.image,
            "updated_date": date.today(),
            "inactive_date": inactive_date,
            "application": required_detail.application,
            "salary": salary,
            "batch": required_detail.batch
        }

        # Return the response with status code 200
        return DataSetOut(status_code=200, details=data)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=403, detail=str(e))
if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    uvicorn.run(app="main:app", host="", port=int(os.getenv("PORT")), reload=True)
