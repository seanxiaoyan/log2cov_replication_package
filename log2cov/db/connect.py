from pymongo import MongoClient
import os

class Connect(object):
    @staticmethod    
    def get_connection():
        client = MongoClient(
        host=os.environ["MONGO_HOST"],
        port=int(os.environ["MONGO_PORT"])
    )
        return client