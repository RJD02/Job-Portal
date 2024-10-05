from sqlalchemy import Boolean,Column,Integer,String
from database import Base
from sqlalchemy import LargeBinary

class admin(Base):
    __tablename__ = 'admin_table'

    id = Column(Integer,primary_key=True)
    username = Column(String(100),unique=True)
    password = Column(String(500))

class CompanyDetails(Base):
    __tablename__ = 'details'

    id = Column(Integer,primary_key=True,autoincrement=True)
    company = Column(String(100))
    designation = Column(String(100))
    description= Column(String)
    image = Column(String)
