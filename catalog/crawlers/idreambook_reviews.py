import requests
import json
import base64
from pymongo import MongoClient
from mylibrary import settings

class CriticReviewsAPI():
    def __init__(self):
        # client = MongoClient("mongodb://localhost:27017")
        client = MongoClient("mongodb+srv://mylibrary:"+settings.MONGO_PASSWORD+"@cluster0.tkgmm.mongodb.net/mylibrary?retryWrites=true&w=majority")
        db = client["mylibrary"]
        self.books_coll = db["books_info"]
        self.review_coll = db["book_reviews"]
        self.api_key = settings.IDREAM_BOOKS_API_KEY

    def get_critics_review_data(self, review_json, book_data):
        temp_data = {}
        temp_data["book_title"] =  book_data["actual_book_title"]
        temp_data["author"] = book_data["authors"][0]
        temp_data["isbn_13"] = book_data["isbn_13"]
        temp_data["idream_critics_review"] = []
        if review_json["total_results"] > 0 and review_json["book"].get("critic_reviews",[]):
            for each_review in review_json["book"]["critic_reviews"]:
                temp_data["idream_critics_review"].append({
                    "source" : each_review["source"],
                    "review_url" : each_review["review_link"],
                    "summary" : each_review["snippet"],
                    "star_rating": each_review["star_rating"],
                    "review_date" : each_review["review_date"]
                })
        mongo_review_data = self.review_coll.find_one({"isbn_13":temp_data["isbn_13"]},{"_id":0})
        if mongo_review_data:
            mongo_review_data["idream_critics_review"] = temp_data["idream_critics_review"]
            self.review_coll.update({"isbn_13":temp_data["isbn_13"]},mongo_review_data)
        else:
            self.review_coll.insert_one(temp_data)
        return temp_data["idream_critics_review"]

    def get_critics_review(self, book_data):
        isbn_13 = book_data["isbn_13"]
        critics_review = []
        review_url = "http://idreambooks.com/api/books/reviews.json?q="+isbn_13+"&key="
        reviews = self.review_coll.find_one({"isbn_13":isbn_13},{"_id":0})
        if reviews and "idream_critics_review" in reviews:
            critics_review = reviews["idream_critics_review"]
        else:
            try:
                review_data = requests.get(review_url+self.api_key)
                if review_data.status_code == 200:
                    review_json = review_data.json()
                    critics_review = self.get_critics_review_data(review_json, book_data)
            except Exception as e:
                print("Exception in IDream Book get_critic_reviews\n",e)
        return critics_review
