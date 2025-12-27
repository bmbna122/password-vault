from fastapi import FastAPI, Form, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import os, requests, secrets

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
app.add_middleware(SlowAPIMiddleware)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
Instrumentator().instrument(app).expose(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY_MIN = 60

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def supabase(path, method="get", json=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    return requests.request(method, f"{SUPABASE_URL}/rest/v1/{path}", headers=headers, json=json)

def create_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MIN)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/register")
@limiter.limit("10/minute")
def register(request: Request, email: str = Form(...), password: str = Form(...)):
    hashed = pwd_context.hash(password)
    res = supabase("users", "post", {"email": email, "password_hash": hashed})
    if not res.ok:
        raise HTTPException(400, "User already exists")
    return {"status": "registered"}

@app.post("/login")
@limiter.limit("10/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    res = supabase(f"users?email=eq.{form.username}", "get")
    users = res.json()
    if not users:
        raise HTTPException(401, "Invalid credentials")
    user = users[0]
    if not verify_password(form.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(user["id"]), "token_type": "bearer"}

@app.post("/generate")
@limiter.limit("10/minute")
def generate(request: Request, token: str = Depends(oauth2_scheme), username: str = Form(...), notes: str = Form(...)):
    user_id = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])["sub"]
    password = secrets.token_urlsafe(16)
    res = supabase("vault", "post", {"user_id": user_id, "username": username, "notes": notes, "password": password})
    if not res.ok:
        raise HTTPException(500, "DB error")
    return {"password": password}

@app.get("/vault")
def list_vault(token: str = Depends(oauth2_scheme)):
    uid = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])["sub"]
    return supabase(f"vault?user_id=eq.{uid}", "get").json()

@app.delete("/vault/{vid}")
def delete_secret(vid: str, token: str = Depends(oauth2_scheme)):
    jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return supabase(f"vault?id=eq.{vid}", "delete").json()

@app.post("/rotate/{vid}")
def rotate(vid: str, token: str = Depends(oauth2_scheme)):
    uid = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])["sub"]
    new_pass = secrets.token_urlsafe(16)
    supabase(f"vault?id=eq.{vid}&user_id=eq.{uid}", "patch", {"password": new_pass})
    return {"password": new_pass}

