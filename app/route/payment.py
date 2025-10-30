from bakong_khqr import KHQR
from fastapi import APIRouter , HTTPException 
from app.models import CartQRRequest
from bson.objectid import ObjectId
from app.config import get_database

router = APIRouter()
# Create an instance of KHQR with Bakong Developer Token:
khqr = KHQR("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiODVjNWNmN2NkZmMzNGI0MiJ9LCJpYXQiOjE3NjA3NTkxNzEsImV4cCI6MTc2ODUzNTE3MX0.JzqtM49Evjn5FgzNz6z3pCKFay2L7m0rrPzhRd_bKc8")



@router.post("/generate_qr")
async def generate_payment_qr(products: CartQRRequest):
    """
    Generate a Bakong KHQR Payment QR Code from JSON input.
    """
    try:
        amount = 0
        db = get_database()
        product_collection = db.get_collection("products")
        cart_data = product_collection.find({"_id":  {"$in": [ ObjectId(item) for item in products.product_ids]}})
        async for product in cart_data:
            amount += product["price"]
        qr = khqr.create_qr(
            bank_account='sathyarak_keo@aclb',
            merchant_name='NEW GENERATION',
            merchant_city='Phnom Penh',
            amount= amount,
            currency='KHR',
            store_label='RAKShop',
            phone_number='85581451884',
            bill_number='TRX01234567',
            terminal_label='Cashier-01',
            static=False
        )

        payment_collection = db.get_collection("payments")
        await payment_collection.insert_one({
            "qr_data": qr,
            "amount": amount
        })
        png_base64_uri = khqr.qr_image(qr, format="base64_uri")
        return {"qr_image_base64_uri": png_base64_uri}

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error generating QR:", e)
        raise HTTPException(status_code=500, detail="Failed to generate QR code.")
@router.get("/chceck_payment_status")
async def generate_payment_qr():
    db = get_database()
    payment_collection = db.get_collection("payments")
    qr = await payment_collection.find_one({"amount":100})
    md5 = khqr.generate_md5(qr["qr_data"])
# Check Transaction paid or unpaid:
    payment_status = khqr.check_payment(md5)
    print(payment_status)


    return {"payment_status": payment_status, "md5": md5, "qrstring": qr}

