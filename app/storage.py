import time
import os
from functools import lru_cache
from pymongo import MongoClient
from bson.objectid import ObjectId

class ReceiptStorage:
    # Iniitializaiton of MongoDB connection
    def __init__(self):
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/')
        # mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(mongo_uri)
        self.db = self.client.receipt_processor
        self.receipts = self.db.receipts
        self.points = self.db.points

    # Add a receipt to the document
    def add_receipt(self, receipt_id, receipt):
        receipt['_id'] = receipt_id
        self.receipts.insert_one(receipt)
        return receipt_id
    
    # Delete the _id field before returning mongo db specific fields
    # which might not be serialized
    def get_receipt(self, receipt_id):
        receipt = self.receipts.find_one({'_id': receipt_id})
        if receipt:
            receipt_id = receipt['_id']
            del receipt['_id']
            return receipt
        return None

    # Updating existing document if it exists else
    # it will create and update
    def cache_points(self, receipt_id, points):
        self.points.update_one({'_id': receipt_id}, {'$set': {'points': points}}, upsert=True)
    
    # Get the points if cahced else return None            
    def get_cached_points(self, receipt_id):
        cached_doc = self.points.find_one({'_id': receipt_id})
        if cached_doc:
            return cached_doc.get('points')
        return None
    # Closing MongoDB cnnection
    def close(self):
        if self.client:
            self.client.close()

# Singleton instance of Receipt Store
receipt_store = ReceiptStorage()