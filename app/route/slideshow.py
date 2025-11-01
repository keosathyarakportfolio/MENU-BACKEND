from fastapi import APIRouter, HTTPException, UploadFile, Form
from fastapi.responses import FileResponse
from app.config import get_database
from bson import ObjectId
import os
import shutil

router = APIRouter()
db = get_database()
slideshow_collection = db["slideshows"]

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.get("/getslides")
async def get_slides():
    slides = []
    async for slide in slideshow_collection.find().sort("_id", -1):  # -1 = descending
        slide["_id"] = str(slide["_id"])
        slides.append(slide)
    return slides


# 🆕 Create slide with image upload
@router.post("/insertslides")
async def create_slide(description: str = Form(...), image: UploadFile = None):
    filename = None
    if image:
        filename = f"{ObjectId()}_{image.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    slide = {"description": description, "image": filename}
    result = await slideshow_collection.insert_one(slide)

    slide["_id"] = str(result.inserted_id)
    return slide


# ✏️ Update slide with optional new image
@router.put("/updateslides/{slide_id}")
async def update_slide(slide_id: str, description: str = Form(...), image: UploadFile = None):
    slide = await slideshow_collection.find_one({"_id": ObjectId(slide_id)})
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    update_data = {"description": description}

    # If new image uploaded, replace old one
    if image:
        filename = f"{ObjectId()}_{image.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # delete old file if exists
        if slide.get("image"):
            old_path = os.path.join(UPLOAD_FOLDER, slide["image"])
            if os.path.exists(old_path):
                os.remove(old_path)

        update_data["image"] = filename

    await slideshow_collection.update_one({"_id": ObjectId(slide_id)}, {"$set": update_data})

    updated = await slideshow_collection.find_one({"_id": ObjectId(slide_id)})
    updated["_id"] = str(updated["_id"])
    return updated


# ❌ Delete slide
@router.delete("/deleteslides/{slide_id}")
async def delete_slide(slide_id: str):
    slide = await slideshow_collection.find_one({"_id": ObjectId(slide_id)})
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    if slide.get("image"):
        old_path = os.path.join(UPLOAD_FOLDER, slide["image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    await slideshow_collection.delete_one({"_id": ObjectId(slide_id)})
    return {"message": "Slide deleted successfully"}
