import requests
import json
import base64
from pymongo import MongoClient, DESCENDING
from mylibrary import settings
from datetime import datetime, timezone
from collections import OrderedDict
from .google_books_api import GoogleBooksAPIData

class NYTimesAPI():
    def __init__(self):
        # client = MongoClient("mongodb://localhost:27017")
        client = MongoClient("mongodb+srv://mylibrary:"+settings.MONGO_PASSWORD+"@cluster0.tkgmm.mongodb.net/mylibrary?retryWrites=true&w=majority")
        db = client["mylibrary"]
        self.bestsellers_coll = db["nyt_bestsellers_list"]
        self.review_coll = db["book_reviews"]
        self.api_key = settings.NYTIMES_API_KEY

    def create_book_data(self, each_book):
        temp_data = OrderedDict()
        temp_data["title"] = each_book["title"]
        temp_data["author"] = each_book["author"]
        temp_data["book_rank"] = each_book["rank"]
        temp_data["rank_last_week"] = each_book["rank_last_week"]
        temp_data["weeks_on_list"] = each_book["weeks_on_list"]
        temp_data["isbn_10"] = each_book["primary_isbn10"]
        temp_data["isbn_13"] = each_book["primary_isbn13"]
        temp_data["publisher"] = each_book["publisher"]
        temp_data["description"] = each_book["description"]
        temp_data["book_image"] = each_book["book_image"]
        temp_data["buy_links"] = each_book["buy_links"]
        return temp_data

    def format_and_save_data(self, result_json):
        list_data = result_json["results"]
        final_data = OrderedDict()
        final_data["list_name"] = list_data["list_name"]
        final_data["published_date"] = datetime.strptime(list_data["previous_published_date"],"%Y-%m-%d")
        # final_data["previous_published_date"] = datetime.strptime(list_data["previous_published_date"],"%Y-%m-%d")
        final_data["next_published_date"] = datetime.strptime(list_data["published_date"],"%Y-%m-%d")
        final_data["next_publish_timestamp"] = int(final_data["next_published_date"].replace(tzinfo=timezone.utc).timestamp())
        final_data["book_list"] = OrderedDict()
        for each_book in list_data["books"]:
            string_to_encode = each_book["primary_isbn13"]
            unique_id =  str(base64.b64encode(string_to_encode.encode("utf-8")),"utf-8")
            final_data["book_list"][unique_id] = self.create_book_data(each_book)
        ### Save data in mongo
        self.bestsellers_coll.insert_one(final_data)
        return final_data

    def get_bestsellers_list(self, current_date_str,genre):
        bestseller_list = []
        ## Getting Data only f/or fiction - can be extended to non fiction as well
        if genre == "fiction":
            bestseller_url = "https://api.nytimes.com/svc/books/v3/lists/"+current_date_str+"/hardcover-fiction.json?api-key="
        elif genre == "non_fiction":
            bestseller_url = "https://api.nytimes.com/svc/books/v3/lists/"+current_date_str+"/hardcover-nonfiction.json?api-key="
        result = requests.get(bestseller_url+self.api_key)
        if result.status_code == 200:
            result_json = result.json()
            bestseller_list = self.format_and_save_data(result_json)
        else:
            print("Error in getting list")
        return bestseller_list

    def nyt_bestsellers_list(self, genre):
        ## Step1 - Get Today's Date
        current_date = datetime.now()
        current_date_str = current_date.strftime("%Y-%m-%d")
        current_timestamp = int(current_date.replace(tzinfo=timezone.utc).timestamp())
        ### Now get latest data from mongo
        latest_record = list(self.bestsellers_coll.find({"list_name": "Hardcover Fiction" if genre=="fiction" else "Hardcover Nonfiction"}).sort("next_publish_timestamp",DESCENDING).limit(1))
        if latest_record:
            ## Check if current date is greater than next publish date
            if current_timestamp > latest_record[0]["next_publish_timestamp"]:
                nytimes_list = self.get_bestsellers_list(current_date_str, genre)
            else:
                nytimes_list = latest_record[0]
        else:
            nytimes_list = self.get_bestsellers_list(current_date_str,genre)
        return nytimes_list

    def get_review_data(self, review_json, google_books_data):
        temp_data = {}
        temp_data["book_title"] =  google_books_data["actual_book_title"]
        temp_data["author"] = google_books_data["authors"][0]
        temp_data["isbn_13"] = google_books_data["isbn_13"]
        temp_data["nyt_review"] = []
        if review_json["num_results"] > 0:
            for each_review in review_json["results"]:
                temp_data["nyt_review"].append({
                    "review_url" : each_review["url"],
                    "review_by" :  each_review["byline"],
                    "summary" : each_review["summary"],
                    "publication_date" : each_review["publication_dt"]
                })

        mongo_review_data = self.review_coll.find_one({"isbn_13":temp_data["isbn_13"]},{"_id":0})
        if mongo_review_data:
            mongo_review_data["nyt_review"] = temp_data["nyt_review"]
            self.review_coll.update({"isbn_13":temp_data["isbn_13"]},mongo_review_data)
        else:
            self.review_coll.insert_one(temp_data)
        return temp_data["nyt_review"]

    def get_book_review(self, google_books_data):
        nyt_review = []
        isbn_13 = google_books_data["isbn_13"]
        review_url = "https://api.nytimes.com/svc/books/v3/reviews.json?isbn="+isbn_13+"&api-key="
        reviews = self.review_coll.find_one({"isbn_13":isbn_13},{"_id":0})
        if reviews and "nyt_review" in reviews:
            nyt_review = reviews["nyt_review"]
        else:
            try:
                review_data = requests.get(review_url+self.api_key)
                if review_data.status_code == 200:
                    review_json = review_data.json()
                    nyt_review = self.get_review_data(review_json, google_books_data)
            except Exception as e:
                print("Error in Ny times API - get_book_review:\n",e)
        return nyt_review


# if __name__ == '__main__':
#     NYTimesAPI().main()
