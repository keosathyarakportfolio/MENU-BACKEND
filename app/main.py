from fastapi import FastAPI
from .route import setup
from .middleware import token_check_middleware

app = FastAPI()

app.middleware("http")(token_check_middleware)

@app.on_event("startup")
async def on_startup():
    await setup(app)