import os
import shutil
import uuid
from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Query
from bson.objectid import ObjectId
from app.config import get_database

UPLOAD_FOLDER = "uploads"  # Make sure this folder exists
router = APIRouter()


# --- Helper: Delete image file safely ---
def delete_image_file(filename: str):
    if filename:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)


# --- INSERT PRODUCT ---
@router.post("/insertproduct")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    image: UploadFile = File(None)
):
    db = get_database()
    product_collection = db.get_collection("products")

    filename = None
    if image:
        filename = f"{uuid.uuid4()}_{image.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    product_data = {
        "name": name,
        "description": description,
        "price": price,
        "image": filename
    }

    result = await product_collection.insert_one(product_data)
    created_product = await product_collection.find_one({"_id": result.inserted_id})
    created_product["_id"] = str(created_product["_id"])
    return created_product


# --- GET ALL PRODUCTS WITH PAGINATION ---
@router.get("/getproduct")
async def get_all_products(page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    """
    Get products with pagination (newest to oldest).
    - page: current page number (default 1)
    - limit: items per page (default 10)
    """
    db = get_database()
    product_collection = db.get_collection("products")

    skip = (page - 1) * limit
    total_count = await product_collection.count_documents({})

    # Sort by _id descending (newest first)
    cursor = product_collection.find().sort("_id", -1).skip(skip).limit(limit)

    products = []
    async for product in cursor:
        product["_id"] = str(product["_id"])
        products.append(product)

    total_pages = (total_count + limit - 1) // limit  # ceiling division

    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_count": total_count,
        "products": products
    }



# --- UPDATE PRODUCT ---
@router.put("/updateproduct/{product_id}")
async def update_product(
    product_id: str,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    image: UploadFile = File(None)
):
    db = get_database()
    product_collection = db.get_collection("products")

    # Get current product
    existing_product = await product_collection.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = {"name": name, "description": description, "price": price}

    # If new image uploaded, replace it
    if image:
        # Delete old image if exists
        old_image = existing_product.get("image")
        delete_image_file(old_image)

        # Save new image
        filename = f"{uuid.uuid4()}_{image.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        update_data["image"] = filename

    # Update database
    await product_collection.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
    updated_product = await product_collection.find_one({"_id": ObjectId(product_id)})
    updated_product["_id"] = str(updated_product["_id"])
    return updated_product


# --- DELETE PRODUCT ---
@router.delete("/deleteproduct/{product_id}")
async def delete_product(product_id: str):
    db = get_database()
    product_collection = db.get_collection("products")

    product = await product_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete image file if exists
    delete_image_file(product.get("image"))

    # Delete from DB
    result = await product_collection.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 1:
        return {"status": "success", "message": f"Product with ID '{product_id}' deleted successfully."}
    else:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found")
