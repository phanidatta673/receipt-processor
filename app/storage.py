import time
import os
import json
import hashlib
from functools import lru_cache
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure
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

        # Create an index on receipt_hash
        try:
            # Check existing documents without a receipt_hash
            existing_docs = self.receipts.count_documents({"receipt_hash": {"$exists": False}})
            
            if existing_docs == 0:
                # Create the unique index
                self.receipts.create_index([("receipt_hash", ASCENDING)], unique=True, sparse=True)
            else:
                # There are existing documents null receipt_hash
                self.receipts.create_index([("receipt_hash", ASCENDING)], sparse=True)
        except (DuplicateKeyError, OperationFailure) as e:
            # Index might already exist or other issue
            print(f"Note: Index creation issue: {e}")
            pass

    # Geenrate a unique hash for a receipt
    def generate_receipt_hash(self, receipt):
        receipt_copy = receipt.copy()
        if 'items' in receipt_copy:
            receipt_copy['items'] = sorted(receipt_copy['items'], key=lambda x: x.get('shortDescription','')+x.get('price',''))
        
        # Convert to a standardized string format
        receipt_string = json.dumps(receipt_copy, sort_keys=True)
        # Hashing the standardized string for consistent hashing
        return hashlib.sha256(receipt_string.encode('utf-8')).hexdigest()
    
    # Add a receipt to the document
    def add_receipt(self, receipt_id, receipt):
        receipt_hash = self.generate_receipt_hash(receipt)

        # Check if the receipt exists
        receipt_exists = self.receipts.find_one({"receipt_hash": receipt_hash})
        
        if receipt_exists:
            return receipt_exists['_id']
        
        receipt['_id'] = receipt_id
        receipt['receipt_hash'] = receipt_hash
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