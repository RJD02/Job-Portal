from sqlalchemy import Column,Integer,String,TIMESTAMP, Text, DATE
from database import Base
class admin(Base):
    __tablename__ = 'admin_table'

    id = Column(Integer,primary_key=True)
    username = Column(String(100),unique=True)
    password = Column(String(500))
    token = Column(Text)
    expiry = Column(TIMESTAMP)

class CompanyDetails(Base):
    __tablename__ = 'details'

    id = Column(Integer,primary_key=True,autoincrement=True)
    company = Column(String(100))
    designation = Column(String(100))
    description= Column(String)
    image = Column(String)
    updated_date = Column(DATE, default="CURRENT_DATE")  # Defaults to current date
    inactive_date = Column(DATE)  # This can be NULL
    application = Column(String(150))
    salary = Column(String(20))

