from fastapi import Request, HTTPException
from jwt import decode, exceptions
from app.config import get_database

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

async def token_check_middleware(request: Request, call_next):
    if not request.url.path.startswith("/uploads") and request.url.path not in ["/chceck_payment_status","/login", "/register", "/docs", "/openapi.json", "/getproduct", "/getslides"]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")

        token = auth_header.split(" ")[1]
        try:
            payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check if user exists in the database
            users_collection = get_database().get_collection("user")
            user = await users_collection.find_one({"user_id": user_id})
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")

        except exceptions.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    response = await call_next(request)
    return response
