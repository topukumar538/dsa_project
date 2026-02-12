from fastapi import FastAPI, Form, Request, Depends
from typing import Annotated
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn

from database import (
    init_db,
    get_db,
    authenticate_user,
    create_user as db_create_user,
    get_user_by_username,
    get_user_by_email,
    get_password_hash, verify_password, User
)

from utility import validate_password, validate_username, validate_email, fetch_user, get_user_data, fetch_admin


db_dependency = Annotated[Session, Depends(get_db)]

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on app startup"""
    init_db()


# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display the login form"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Validate login credentials and redirect"""

    # Authenticate user from database using email
    user = authenticate_user(db, email, password)

    if user:
        return RedirectResponse(url=f"/welcome?email={user.email}", status_code=303)
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password", "email": email},
        )


@app.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request, email: str):
    """Display welcome page with news after successful login"""
    if not email:
        return RedirectResponse(url="/", status_code=303)

    user = fetch_user(email)
    if user:

        return templates.TemplateResponse(
            "welcome.html",
            {
                "request": request,
                "username": user.username,
                "email": user.email,
                "points": user.points,
            },
        )
    else:
        return templates.TemplateResponse(
            "welcome.html",
            {
                "request": request,
                "username": "hello",
                "email": "hello@gmail.com",
                "points": 0,
            },
        )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display the registration form"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": username_error,
                "username": username,
                "email": email,
            },
        )

    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": email_error,
                "username": username,
                "email": email,
            },
        )

    existing_email = get_user_by_email(db, email)
    if existing_email:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Email already registered. Please use a different email or login.",
                "username": username,
                "email": email,
            },
        )

    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": password_error,
                "username": username,
                "email": email,
            },
        )

    # Check if passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Passwords do not match",
                "username": username,
                "email": email,
            },
        )

    try:
        db_create_user(db, username, email, password)

        return templates.TemplateResponse(
            "welcome.html",
            {"request": request, "username": username, "email": email, "points": 0},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": f"An error occurred while creating your account. Please try again.",
                "username": username,
                "email": email,
            },
        )


#for change password
@app.get("/update", response_class=HTMLResponse)
async def update(request: Request):
    return templates.TemplateResponse(
        "update.html",
        {"request": request}
    )


@app.post("/update")
async def update_data(request: Request, email: str = Form(...), 
                      old_password: str = Form(...), new_password: str = Form(...), 
                      confirm_password: str = Form(...), db: Session = Depends(get_db)):
    
    user = fetch_user(email)
    
    if not user:
        return templates.TemplateResponse("update.html", {
            "request":request,
            "email":email,
            "error": "please! enter valid email 1"
        })

    if not verify_password(old_password , user.hashed_password):
        return templates.TemplateResponse("update.html", {
            "request":request,
            "email":email,
            "error": "please! enter valid passwor 2"
        })
    is_valid_password, password_error = validate_password(new_password)
    if not is_valid_password:
        return templates.TemplateResponse("update.html", {
            "request":request,
            "email":email,
            "error": password_error
        })  
    
    if new_password != confirm_password:
        return templates.TemplateResponse("update.html", {
            "request":request,
            "email":email,
            "error": "please! enter new password and confirm password equal 4"
        })

    db.query(User).filter(User.email == email).update({"hashed_password": get_password_hash(new_password)})
    db.commit()
    return RedirectResponse(url=f"/welcome?email={user.email}", status_code=303)





#to login adminsite
@app.get("/loginadmin", response_class=HTMLResponse)
async def log_admin(request: Request):
    return templates.TemplateResponse(
        "log_admin.html", {"request": request}
    )

@app.post("/loginadmin")
async def login_admin(request: Request, email:str = Form(...), password: str = Form(...)):
    admin = fetch_admin(email)
    if not admin:
        return templates.TemplateResponse("log_admin.html", {
            "request":request,
            "email":email,
            "error": "please! enter valid email 1"
        })
    

    if not verify_password(password , admin.hashed_password):
        return templates.TemplateResponse("log_admin.html", {
            "request":request,
            "email":email,
            "error": "please! enter valid passwor 2"
        })
    

    return RedirectResponse(url=f"/admin?email={admin.email}", status_code=303)





@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, email: str):
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "email": email
        }
    )



@app.get("/adminuser", response_class=HTMLResponse)
async def admin_to_user(request: Request):
    data = get_user_data()
    return templates.TemplateResponse(
        "userdata.html", {
            "request":request,
            "data": data
        }
    )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
