from pydantic import BaseModel
from typing import  Union
from datetime import date

class login_data(BaseModel):
    username: str
    password: str

class detailing(BaseModel):
    company: str
    designation: str
    description: str
    image: str
    updated_date: Union[None,date]
    inactive_date: Union[None,date]
    application: str
    salary: Union[None,str]

class DataSetOut(BaseModel):
    status_code: int
    details: Union[str,dict]