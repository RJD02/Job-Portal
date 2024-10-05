from pydantic import BaseModel
from typing import  Union
class login_data(BaseModel):
    username: str
    password: str

class detailing(BaseModel):
    company: str
    designation: str
    description: str
    image: str

class DataSetOut(BaseModel):
    status_code: int
    details: Union[str,dict]