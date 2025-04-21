from pydantic import BaseModel, Field, validator
from typing import List
import re
from datetime import datetime

class Item(BaseModel):
    shortDescription: str
    price: str

    @validator('shortDescription')
    def validate_description(cls, value):
        if not re.match(r'^[\w\s\-]+$', value):
            raise ValueError('Invalid short description format')
        return value
    
    @validator('price')
    def validate_price(cls, value):
        if not re.match(r'^\d+\.\d{2}$', value):
            raise ValueError('Invalid price, must be in format X.XX')
        return value

class Receipt(BaseModel):
    retailer: str
    purchaseDate: str
    purchaseTime: str
    items: List[Item]
    total: str

    @validator('retailer')
    def validate_retailer(cls, value):
        if not re.match(r'^[\w\s\-&]+$', value):
            raise ValueError('Invalid retailer name format')
        return value
    
    @validator('purchaseDate')
    def validate_date(cls,value):
        try:
            datetime.strptime(value,'%Y-%m-%d')
        except ValueError:
            raise ValueError('Invalid date must be in format YYYY-MM-DD')
        return value
    
    @validator('purchaseTime')
    def validate_time(cls,value):
        try:
            datetime.strptime(value, '%H:%M')
        except ValueError:
            raise ValueError('Invalid time must be in format HH:MM')
        return value
    
    @validator('total')
    def validate_total(cls, value):
        if not re.match(r'^\d+\.\d{2}$', value):
            raise ValueError('Invalid total must be in format X.XX')
        return value

class ReceiptResponse(BaseModel):
    id: str

class PointsResponse(BaseModel):
    points: int