from sqlalchemy import create_engine, Column, Integer, String, DateTime, REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime
from typing import Annotated
from fastapi import Depends

DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index = True, nullable= False)
    hashed_password = Column(String, nullable=False)
    points = Column(REAL, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key = True, index =True)
    username = Column(String, nullable= False)
    email = Column(String, unique=True, index = True, nullable = False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)



# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

#for admin to access user site
def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "admin@example.com").first() #admin email to login user site
        if not admin_user:
            admin_user = User(
                username = 'admin',
                email = "admin@example.com",
                hashed_password = pwd_context.hash("admin123")
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()


    #admin site 
    try:
        admin_user = db.query(Admin).filter(Admin.email == "admin@gmail.com").first()
        if not admin_user:
            admin_user = Admin(
                username = "admin",
                email = "admin@gmail.com",
                hashed_password = get_password_hash("admin123")
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()














# Password utilities
def verify_password(plain_password: str, hashed_password) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# User operations
def get_user_by_username(db : db_dependency, username: str):
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: db_dependency, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: db_dependency, username: str, email: str, password: str):
    """Create a new user"""
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password, points=0) # default point 0
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: db_dependency, email: str, password: str):
    """Authenticate user credentials using email"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
