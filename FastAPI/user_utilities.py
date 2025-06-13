from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "postgresql://postgres:hackathon@145.249.115.97:5432/DataBase"

class UserUtilities(BaseModel):
    user_id: int
    cold_water: float = 0
    hot_water: float = 0
    electricity: float = 0
    heating: float = 0
    water_drainage: float = 0
    housing_maintenance: float = 0
    capital_repair: float = 0

@app.post("/utilities")
async def create_utilities(utilities: UserUtilities):
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute(
            """INSERT INTO user_utilities 
            (user_id, cold_water, hot_water, electricity, heating, 
             water_drainage, housing_maintenance, capital_repair)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            utilities.user_id, utilities.cold_water, utilities.hot_water,
            utilities.electricity, utilities.heating, utilities.water_drainage,
            utilities.housing_maintenance, utilities.capital_repair
        )
        await conn.close()
        return {"message": "Utilities data created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
