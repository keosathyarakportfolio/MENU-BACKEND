from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Product(BaseModel):
    name: str
    price: float
    description: str
    images: str  # can be URL or path

# --- Slideshow Model ---
class Slideshow(BaseModel):
    description: str
    image: str  # URL or path

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class CartQRRequest(BaseModel):
    product_ids: list[str]  # e.g. ["671f2a84f8d1e21bdfce5b23", "671f2a84f8d1e21bdfce5b24"]

    