from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import secrets

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "postgresql://postgres:hackathon@145.249.115.97:5432/DataBase"

class User(BaseModel):
    full_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

tokens = {}
user_roles = {}

async def get_db_conn():
    conn = await asyncpg.connect(DB_URL)
    try:
        yield conn
    finally:
        await conn.close()

@app.post("/register")
async def register(user: User, conn: asyncpg.connect = Depends(get_db_conn)):
    try:
        user_id = await conn.fetchval(
            "INSERT INTO users (full_name, email, password) VALUES ($1, $2, $3) RETURNING id",
            user.full_name, user.email, user.password
        )
        
        user_roles[user_id] = "user"
        token = secrets.token_hex(16)
        tokens[token] = user_id
        
        return {
            "token": token,
            "user_id": user_id
        }
    except asyncpg.UniqueViolationError:
        raise HTTPException(400, "Email уже используется")

@app.post("/login")
async def login(credentials: LoginRequest, conn: asyncpg.connect = Depends(get_db_conn)):
    user = await conn.fetchrow(
        "SELECT id FROM users WHERE email = $1 AND password = $2", 
        credentials.email, credentials.password
    )
    
    if not user:
        raise HTTPException(400, "Неверные email или пароль")
    
    user_id = user['id']
    token = secrets.token_hex(16)
    tokens[token] = user_id
    
    return {
        "token": token,
        "user_id": user_id
    }

@app.get("/verify")
async def verify(token: str):
    if token not in tokens:
        raise HTTPException(401, "Неверный токен")
    return {
        "user_id": tokens[token],
        "role": user_roles.get(tokens[token], "user")
    }
