import requests
import json
import base64
from pymongo import MongoClient
from mylibrary import settings

class CriticReviewsAPI():
    def __init__(self):
        client = MongoClient("mongodb://localhost:27017")
        db = client["mylibrary"]
        self.books_coll = db["books_info"]
        self.google_api_key = settings.IDREAM_BOOKS_API_KEY
