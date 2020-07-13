import requests
import json
import base64
from pymongo import MongoClient
from mylibrary import settings

class GoogleBooksAPIData():
    def __init__(self):
        # client = MongoClient("mongodb://localhost:27017")
        client = MongoClient("mongodb+srv://mylibrary:"+settings.MONGO_PASSWORD+"@cluster0.tkgmm.mongodb.net/mylibrary?retryWrites=true&w=majority")
        db = client["mylibrary"]
        self.books_coll = db["books_info"]
        self.google_api_key = settings.GOOGLE_BOOKS_API_KEY

    def get_mongo_data(self, unique_key="", isbn=""):
        book_data = {}
        if unique_key:
            book_data = self.books_coll.find_one({"unique_book_id":unique_key},{"_id":0})
        elif isbn:
            book_data = self.books_coll.find_one({"isbn_13":isbn},{"_id":0})
        return book_data

    def save_mongo_data(self, book_data, nytimes_fiction):
        volume_info = book_data["volumeInfo"]
        data_to_save = {
            "book_title" : volume_info["title"].lower(),
            "actual_book_title" : volume_info["title"],
            "subtitle" : volume_info.get("subtitle",""),
            "authors" : volume_info.get("authors",[]),
            "publisher": volume_info.get("publisher",""),
            "description": volume_info.get("description",""),
            "page_count" : volume_info.get("pageCount",0),
            "average_rating": volume_info.get("averageRating",0),
            "book_image_links" : volume_info.get("imageLinks",{"thumbnail":""}),
            "preview_link" :  volume_info.get("previewLink",""),
            "buy_link" :  volume_info.get("infoLink","")
        }
        if not volume_info.get("categories",[]) and nytimes_fiction:
            data_to_save["genre"] = ["Fiction"]
        else:
            data_to_save["genre"] = volume_info.get("categories",[])
        ## for unique_key
        string_to_encode = data_to_save["book_title"] + " " + " ".join([auth.lower() for auth in data_to_save["authors"]])
        data_to_save["unique_book_id"] = str(base64.b64encode(string_to_encode.encode("utf-8")),"utf-8")
        ### For isbn 10 and isbn 13 numbers
        for indentifier in volume_info["industryIdentifiers"]:
            data_to_save[indentifier["type"].lower()] = indentifier["identifier"]
        #### Saving Data to Mongo #########
        # print(json.dumps(data_to_save))
        self.books_coll.insert_one(data_to_save)
        # print("Data Saved to Mongo")
        return data_to_save

    def get_google_books_data(self, book_title="", author="", isbn=""):
        book_data = {}
        try:
            if book_title and author and not isbn:
                book_url = "https://www.googleapis.com/books/v1/volumes?q=intitle:"
                result = requests.get(book_url+book_title+"&key="+self.google_api_key)
            elif isbn:
                book_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
                result = requests.get(book_url+isbn+"&key="+self.google_api_key)
            if result.status_code == 200:
                result_json = result.json()
                if result_json and result_json["totalItems"] > 0:
                    book_data = result_json["items"][0]
        except Exception:
            print("Error in getting book from api")
        return book_data

    def get_book_data(self, book_title="", author="",isbn="", nytimes_fiction=False):
        saved_book_data = {}
        book_data = {}
        if book_title and author and not isbn:
            string_to_encode = book_title.lower() + " " + author.lower()
            unique_key = str(base64.b64encode(string_to_encode.encode("utf-8")),"utf-8")
            ## search data in mongo using the unique key
            saved_book_data = self.get_mongo_data(unique_key=unique_key)
            ## if the record is not found, then scrap the data from api
            if not saved_book_data:
                book_data = self.get_google_books_data(book_title=book_title, author=author)
                if book_data:
                    saved_book_data = self.save_mongo_data(book_data)

        elif isbn and not book_title and not author:
            saved_book_data = self.get_mongo_data(isbn=isbn)
            if not saved_book_data:
                book_data = self.get_google_books_data(isbn=isbn)
                if book_data:
                    saved_book_data = self.save_mongo_data(book_data, nytimes_fiction)
        return saved_book_data

# if __name__ == '__main__':
#     book_title = "the fabric of the cosmos"
#     author = "brian greene"
#     GoogleBooksAPIData().get_book_data(book_title, author)
