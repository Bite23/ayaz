from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
import asyncpg
from typing import List, Dict, Any

router = APIRouter(
    prefix="/api",
    tags=["User Profile"]
)

DB_URL = "postgresql://postgres:hackathon@145.249.115.97:5432/DataBase"

class PersonalAccount(BaseModel):
    account_number: str
    address: str
    user_id: int
    area: float
    residents_count: int
    management_company: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    accounts: List[Dict[str, Any]]

async def verify_token(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    if token == "":
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    operation_id="get_user_profile_with_accounts"
)
async def get_user_profile(user_id: int, token: str = Depends(verify_token)):
    try:
        conn = await asyncpg.connect(DB_URL)
        user = await conn.fetchrow(
            "SELECT id, full_name, email FROM users WHERE id = $1",
            user_id
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        accounts = await conn.fetch(
            "SELECT * FROM personal_accounts WHERE user_id = $1",
            user_id
        )
        
        await conn.close()
        accounts_list = [dict(account) for account in accounts]
        
        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "accounts": accounts_list
        }
    except Exception as e:
        raise HTTPException(500, f"Ошибка с DB: {str(e)}")

@router.get(
    "/accounts/{account_number}",
    response_model=PersonalAccount,
    operation_id="get_specific_account"
)
async def get_account_details(account_number: str, token: str = Depends(verify_token)):
    try:
        conn = await asyncpg.connect(DB_URL)
        account = await conn.fetchrow(
            "SELECT * FROM personal_accounts WHERE account_number = $1",
            account_number
        )
        
        await conn.close()
        
        if not account:
            raise HTTPException(status_code=404, detail="Лицевой счет не найден")
            
        return dict(account)
    except Exception as e:
        raise HTTPException(500, f"Ошибка с DB: {str(e)}")