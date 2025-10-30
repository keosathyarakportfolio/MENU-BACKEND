import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_DETAILS = os.getenv("connectstring")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.get_database(os.getenv("database"))

def get_database():
    return database