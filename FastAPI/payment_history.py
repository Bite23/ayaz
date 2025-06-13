from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "postgresql://postgres:hackathon@145.249.115.97:5432/DataBase"

MULTIPLIERS = {
    "cold_water": Decimal('35.34'),
    "hot_water": Decimal('126.58'),
    "electricity": Decimal('6.6'),
    "heating": Decimal('2100'),
    "water_drainage": Decimal('28'),
    "housing_maintenance": Decimal('27'),
    "capital_repair": Decimal('11')
}

class SimplePaymentResponse(BaseModel):
    id: int
    total_amount: float
    payment_date: datetime

class TotalAmountResponse(BaseModel):
    user_id: int
    total_payments: float
    payment_count: int

@app.post("/calculate-and-pay/{user_id}", response_model=SimplePaymentResponse)
async def calculate_and_pay(user_id: int):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        record = await conn.fetchrow(
            "SELECT * FROM user_utilities WHERE user_id = $1", 
            user_id
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Данные пользователя не найдены")

        existing_payment = await conn.fetchrow(
            """SELECT id, total_amount, payment_date FROM payment_history 
            WHERE user_utilities_id = $1 AND user_id = $2""",
            record['id'], user_id
        )
        
        if existing_payment:
            return {
                "id": existing_payment["id"],
                "total_amount": existing_payment["total_amount"],
                "payment_date": existing_payment["payment_date"]
            }

        total = Decimal('0')
        for field, multiplier in MULTIPLIERS.items():
            value = record.get(field, Decimal('0')) or Decimal('0')
            total += value * multiplier

        payment = await conn.fetchrow(
            """INSERT INTO payment_history 
            (user_utilities_id, user_id, total_amount, payment_date)
            VALUES ($1, $2, $3, $4)
            RETURNING id, total_amount, payment_date""",
            record['id'],
            user_id,
            float(round(total, 2)),
            datetime.now()
        )

        return {
            "id": payment["id"],
            "total_amount": payment["total_amount"],
            "payment_date": payment["payment_date"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        if conn:
            await conn.close()

@app.get("/payment-history/{user_id}", response_model=List[SimplePaymentResponse])
async def get_payment_history(user_id: int):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        
        payments = await conn.fetch(
            """SELECT id, total_amount, payment_date FROM payment_history 
            WHERE user_id = $1 ORDER BY payment_date DESC""",
            user_id
        )
        
        return [
            {
                "id": p["id"],
                "total_amount": p["total_amount"],
                "payment_date": p["payment_date"]
            }
            for p in payments
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()

@app.get("/total-payments/{user_id}", response_model=TotalAmountResponse)
async def get_total_payments(user_id: int):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        
        result = await conn.fetchrow(
            """SELECT COUNT(id) as count, COALESCE(SUM(total_amount), 0) as total 
            FROM payment_history WHERE user_id = $1""",
            user_id
        )
        
        return {
            "user_id": user_id,
            "total_payments": float(result["total"]) if result["total"] else 0.0,
            "payment_count": result["count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()

@app.delete("/delete-user-data/{user_id}")
async def delete_user_data(user_id: int):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        
        async with conn.transaction():
            payments_to_archive = await conn.fetch(
                "SELECT * FROM payment_history WHERE user_id = $1",
                user_id
            )

            if payments_to_archive:
                await conn.executemany(
                    """INSERT INTO payment_history_archive 
                    (id, user_utilities_id, user_id, total_amount, payment_date, archived_at)
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    [
                        (p["id"], p["user_utilities_id"], p["user_id"], 
                         p["total_amount"], p["payment_date"], datetime.now())
                        for p in payments_to_archive
                    ]
                )
            
            await conn.execute(
                "DELETE FROM payment_history WHERE user_id = $1",
                user_id
            )
            
            await conn.execute(
                "DELETE FROM user_utilities WHERE user_id = $1",
                user_id
            )
            
        return {"message": f"Все данные пользователя {user_id} успешно удалены и архивированы"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()