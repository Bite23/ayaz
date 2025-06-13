from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg

app = FastAPI()
DB_URL = "postgresql://postgres:hackathon@145.249.115.97:5432/DataBase"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PersonalAccount(BaseModel):
    account_number: str
    address: str
    user_id: int
    area: float
    residents_count: int
    management_company: str

async def verify_token(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    if token != "a73d18af36b2be87ee218f241dbea955":
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/accounts/")
async def add_account(account: PersonalAccount, token: str = Depends(verify_token)):
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("""
            INSERT INTO personal_accounts VALUES
            ($1, $2, $3, $4, $5, $6)
            """,
            account.account_number,
            account.address,
            account.user_id,
            account.area,
            account.residents_count,
            account.management_company
        )
        await conn.close()
        return {"message": "Лицевой счет успешно создан!"}
    
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(400, "Аккаунт уже существует!")
    except Exception as e:
        raise HTTPException(500, f"Ошибка с DB: {str(e)}")

@app.get("/accounts/{user_id}")
async def get_accounts(user_id: int, token: str = Depends(verify_token)):
    try:
        conn = await asyncpg.connect(DB_URL)
        accounts = await conn.fetch(
            "SELECT * FROM personal_accounts WHERE user_id = $1",
            user_id
        )
        await conn.close()
        return accounts
    except Exception as e:
        raise HTTPException(500, f"Ошибка с DB: {str(e)}")

@app.delete("/accounts/")
async def delete_account(account_number: str, token: str = Depends(verify_token)):
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute(
            "DELETE FROM personal_accounts WHERE account_number = $1",
            account_number
        )
        await conn.close()
        return {"message": "Лицевой счет успешно удален!"}
    except Exception as e:
        raise HTTPException(500, f"Ошибка с DB: {str(e)}")