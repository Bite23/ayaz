from fastapi import FastAPI
from payment_history import app as payment_app
from personal_accounts import app as accounts_app
from registration_authorization import app as auth_app
from user_utilities import app as utilities_app
from user_profile import router as profile_router

app = FastAPI()

app.include_router(payment_app.router)
app.include_router(accounts_app.router)
app.include_router(auth_app.router)
app.include_router(utilities_app.router)
app.include_router(profile_router)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)