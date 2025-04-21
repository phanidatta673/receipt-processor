from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
import logging
import time
import json
from app.models import Receipt, ReceiptResponse, PointsResponse
from app.storage import receipt_store
from app.utils import calculate_points

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger("receipt-processor")

app = FastAPI(title="Receipt Processor API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())
    logger.info(f"Request started | ID: {request_id} | Method: {request.method} | Path: {request.url.path}")
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        logger.info(f"Request completed | ID: {request_id} | Status: {response.status_code} | Time: {process_time:.4f}s")
        
        return response
    except Exception as e:
        logger.error(f"Request failed | ID: {request_id} | Error: {str(e)}")
        raise

@app.post("/receipts/process", response_model=ReceiptResponse)
async def process_receipt(receipt: Receipt):
    logger.info("Processing new receipt")
    try:
        # Converting Pydantic Receipt model into Python dictionary
        receipt_dict = receipt.dict()
        logger.debug(f"Receipt data: {json.dumps(receipt_dict)}")
        
        # Generation of unique id
        receipt_id = str(uuid.uuid4())
        logger.info(f"Generated receipt ID: {receipt_id}")
        
        # Storing of receipt with id into the receipt store
        actual_receipt_id = receipt_store.add_receipt(receipt_id, receipt_dict)

        if actual_receipt_id!=receipt_id:
            logger.info(f"Duplicate receipt detected, returning existing ID: {actual_receipt_id}")
            return {"id": actual_receipt_id}
        
        logger.debug(f"Receipt stored with ID: {receipt_id}")
        
        # Calculate the cached points
        points = calculate_points(receipt_dict)
        receipt_store.cache_points(receipt_id, points)
        logger.info(f"Points calculated and cached for receipt {receipt_id}: {points} points")
        
        return {"id": receipt_id}
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid receipt. Please verify input.")

@app.get("/receipts/{receipt_id}/points", response_model=PointsResponse)
async def get_points(receipt_id: str):
    logger.info(f"Retrieving points for receipt ID: {receipt_id}")
    
    # Check the cached points
    cached_points = receipt_store.get_cached_points(receipt_id)
    if cached_points is not None:
        logger.debug(f"Retrieved cached points for receipt {receipt_id}: {cached_points}")
        return {"points": cached_points}
    
    # If points not present in cache, check if receipt exists
    receipt = receipt_store.get_receipt(receipt_id)
    if receipt is None:
        logger.warning(f"Receipt not found for ID: {receipt_id}")
        raise HTTPException(status_code=404, detail="No receipt found for that ID.")
    
    # Calculate points
    logger.debug(f"Calculating points for receipt {receipt_id}")
    points = calculate_points(receipt)
    
    # Cache the points for future reference
    receipt_store.cache_points(receipt_id, points)
    logger.info(f"Points calculated and cached for receipt {receipt_id}: {points} points")
    
    return {"points": points}

@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

# Log application startup
@app.on_event("startup")
async def startup_event():
    logger.info("Receipt Processor API started")
    logger.info("MongoDB connected")

    # Log the initial state of the storage
    receipt_count = receipt_store.receipts.count_documents({})
    logger.info(f"Initial storage state: {receipt_count} receipts in database")

# Log application shutdown
@app.on_event("shutdown")
async def shutdown_event():
    receipt_store.close()
    logger.info(f"Receipt Processor API shutting down.")