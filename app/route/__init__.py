from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  # correct import
from .product import router as product_router
from .slideshow import router as slideshow_router
from .login import user_router as login_router
from .payment import router as payment_router
import os

# Make sure the folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

async def setup(app: FastAPI):
    app.include_router(product_router)
    app.include_router(slideshow_router)
    app.include_router(login_router)
    app.include_router(payment_router)
    
    # Mount uploads folder for serving images
    app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
