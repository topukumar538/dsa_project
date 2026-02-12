import re
from database import SessionLocal, User, Admin

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password requirements"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 50:
        return False, "Password must be less than 50 characters"
    return True, ""

def validate_username(username: str) -> tuple[bool, str]:
    """Validate username requirements"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 20:
        return False, "Username must be less than 20 characters"
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address"
    if len(email) > 100:
        return False, "Email must be less than 100 characters"
    return True, ""

def fetch_user(email: str):
    db = SessionLocal()  # need to check what is the difference between all this
    user = db.query(User).filter(User.email == email).first()
    db.close()
    return user



def get_user_data():
    db = SessionLocal()
    try:
        results = db.query(User).all()  # Assuming you have a User model
        return [
    {"name": user.username, "email": user.email, "points": user.points}
    for user in results
]
    finally:
        db.close()
def fetch_admin(email):
    db = SessionLocal()  # need to check what is the difference between all this
    user = db.query(Admin).filter(Admin.email == email).first()
    db.close()
    return user
