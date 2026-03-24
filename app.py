from fastapi import FastAPI,UploadFile,File,Form,Request, HTTPException, APIRouter, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from jose import jwt, ExpiredSignatureError, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
from decouple import config
from pydantic import BaseModel
from utils.pdf_utils import extract_text_from_pdf, chunk_text
from utils.embeddings import create_embeddings
from utils.vector_store import store_embeddings
from utils.vector_store import search_similar
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
import hashlib
import requests
import uuid
import os
load_dotenv()
DATABASE_URL = "mysql+pymysql://root:Aadithya%40123@localhost/Aadithya"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(hashed)
def verify_password(plain: str, hashed: str):
    hashed_plain = hashlib.sha256(plain.encode()).hexdigest()
    return pwd_context.verify(hashed_plain, hashed)
app = FastAPI()
faiss_index = None
stored_chunks = []
class UserPrompt(BaseModel):
    msg:str
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("FASTAPI_SECRET_KEY")
)
oauth = OAuth()
oauth.register(
    name="google",
    client_id=config("GOOGLE_CLIENT_ID"),
    client_secret=config("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},   
)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
router = APIRouter()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
def get_current_user(token: str = Cookie(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email")
        }
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
@router.get("/auth/login")
async def login(request: Request):
    request.session.clear()
    frontend_url = os.getenv("FRONTEND_URL", "/chat")
    redirect_url = os.getenv("REDIRECT_URL", "http://127.0.0.1:8000/auth")
    request.session["login_redirect"] = frontend_url
    return await oauth.google.authorize_redirect(
        request,
        redirect_url,
        prompt="consent"
    )
@router.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=401, detail="Google authentication failed")
    user = token.get("userinfo")
    if not user:
        raise HTTPException(status_code=401, detail="User info not available")
    user_id = user.get("sub")
    user_email = user.get("email")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid Google authentication")
    access_token = create_access_token(
        data={
            "sub": user_id,
            "email": user_email
        }
    )
    session_id = str(uuid.uuid4())
    redirect_url = request.session.pop("login_redirect", "/chat")
    response = RedirectResponse(url=redirect_url,status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "Login.html",
        {
            "request": request
        }
    )
@app.post("/login", response_class=HTMLResponse)
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    if not user:
        return templates.TemplateResponse(
            "Login.html",
            {
                "request": request, 
                "error": "User does not exist"
            }
        )
    if not verify_password(password, user.password):
        return templates.TemplateResponse(
            "Login.html",
            {
                "request": request, 
                "error": "Incorrect password"
            }
        )
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email
        }
    )
    response = RedirectResponse(url="/chat", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        "Signup.html",
        {
            "request": request
        }
    )
@app.post("/signup",response_class=HTMLResponse)
async def signup(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        db.close()
        return templates.TemplateResponse(
            "Signup.html",
            {
                "request": request, "error": 
                "User already exists"
            }
        )
    try:
        new_user = User(
            id=str(uuid.uuid4()),
            email=email,
            password=hash_password(password)
        )
        db.add(new_user)
        db.commit()
        db.close()
        return templates.TemplateResponse(
            "Signup.html",
            {
                "request": request, 
                "success": "Account created successfully!"
            }
        )
    except Exception as e:
        db.close()
        print("ERROR:", e)   
        return templates.TemplateResponse(
            "Signup.html",
            {
                "request": request,
                "error": str(e)  
            }
        )
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )
@app.post("/chat")
async def ai_chat(data: UserPrompt):
    user_msg = data.msg
    query_embedding = create_embeddings([user_msg])[0]
    indices = search_similar(faiss_index, query_embedding)
    context = " ".join([stored_chunks[i] for i in indices])
    prompt = f"""
    Based on this financial report:
    {context}
    Answer:
    {user_msg}
    """
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv("OPENAI_API_KEY")}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": prompt   
                }
            ]
        }
    )
    result = response.json()
    return {
        "reply": result
    }
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        upload_dir = "data"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        text = extract_text_from_pdf(file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        chunks = chunk_text(text)
        embeddings = create_embeddings(chunks)
        global faiss_index, stored_chunks
        faiss_index = store_embeddings(embeddings)
        stored_chunks = chunks
        return {"message": "PDF processed and indexed successfully"}
    except Exception as e:
        print(f"Error: {e}") 
        raise HTTPException(status_code=500, detail=str(e))
app.include_router(router)