from fastapi import FastAPI, HTTPException, APIRouter, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.models import RegisterRequest, LoginRequest, TokenData
from app.config import get_database
import bcrypt
import uuid
import os
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta

# ------------------ Setup ------------------
user_router = APIRouter()
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
UPLOAD_DIR = "uploads/profile_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files (if using FastAPI app)
# app = FastAPI()
# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ------------------ Token Helper ------------------
def create_access_token(data: dict, expires_delta: int = 60*60*24):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------ Register ------------------
@user_router.post("/register")
async def register_user(user: RegisterRequest):
    users_collection = get_database().get_collection("user")
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    user_id = str(uuid.uuid4())
    token = create_access_token({"user_id": user_id})

    await users_collection.insert_one({
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hashed_pw.decode(),
        "profileImage": "default.png",
        "token": token,
    })
    return {"token": token,
            "name": user.name, 
            "email": user.email, 
            "user_id": user_id
            }

# ------------------ Login ------------------
@user_router.post("/login")
async def login_user(user: LoginRequest):
    users_collection = get_database().get_collection('user')
    found_user = await users_collection.find_one({"email": user.email})

    if not found_user or not bcrypt.checkpw(user.password.encode(), found_user["password"].encode()):
        raise HTTPException(status_code=400, detail="ពាក្យសម្ងាត់ ឬ អ៊ីមែល មិនត្រឹមត្រូវ")

    token = create_access_token({"user_id": found_user["user_id"]})
    await users_collection.update_one({"email": user.email}, {"$set": {"token": token}})

    return {"token": token,
            "name": found_user["name"], 
            "email": found_user["email"], 
            "profileImage": found_user.get("profileImage", "default.png"),
            "user_id": found_user["user_id"]
            }

# ------------------ Logout ------------------
@user_router.post("/logout")
async def logout_user():
    return {"message": "User logged out successfully"}

# ------------------ Update Profile ------------------
@user_router.post("/updateprofile")
async def update_profile(
    name: str = Form(...),
    user_id: str = Form(...),
    oldPassword: str = Form(None),
    newPassword: str = Form(None),
    profileImage: UploadFile = None
):
    users_collection = get_database().get_collection("user")

    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {"name": name}

    # Update password
    if newPassword:
        if not oldPassword or not bcrypt.checkpw(oldPassword.encode(), user["password"].encode()):
            raise HTTPException(status_code=400, detail="ពាក្យសម្ងាត់ចាស់មិនត្រឹមត្រូវ")
        hashed_pw = bcrypt.hashpw(newPassword.encode(), bcrypt.gensalt()).decode()
        update_data["password"] = hashed_pw

    # Update profile image
    if profileImage:
        # Delete old image if exists and not default
        old_image = user.get("profileImage")
        if old_image and old_image != "default.png":
            old_path = os.path.join(UPLOAD_DIR, old_image)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Save new image
        ext = os.path.splitext(profileImage.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(await profileImage.read())
        update_data["profileImage"] = filename

    await users_collection.update_one({"user_id": user_id}, {"$set": update_data})

    return {
        "message": "Profile updated successfully",
        "updated": {
            "name": update_data["name"],
            "profileImage": update_data.get("profileImage", user.get("profileImage"))
        }
    }
@user_router.post("/validate_token")
async def validate_token(token: TokenData):
    payload = verify_token(token.token)
    user_id = payload.get("user_id")
    users_collection = get_database().get_collection("user")
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "profileImage": user.get("profileImage", "default.png")
    }