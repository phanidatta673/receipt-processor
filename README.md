# Receipt Processor Challenge

A FastAPI application that processes receipts and calculates points based on specific rules. The application is containerized using Docker and stores data in MongoDB.

## Features

- Process receipts and calculate points based on specific rules
- Store receipts and points in MongoDB
- RESTful API with FastAPI
- Docker containerization for easy deployment
- Input validation using Pydantic models

## Tech Stack

- Python 3.9
- FastAPI
- MongoDB
- Docker & Docker Compose
- Pydantic for data validation

## Directory Structure

```
.
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── main.py         # FastAPI application
│   ├── models.py       # Pydantic models for validation
│   ├── storage.py      # MongoDB storage interface
│   └── utils.py        # Point calculation logic
├── app.log
├── docker-compose.yml
└── requirements.txt
```

## How to Run

### Prerequisites

- Docker
- Docker Compose

### Running with Docker Compose

1. Clone the repository:
   ```
   git clone <repository-url>
   cd receipt-processor
   ```

2. Start the application with Docker Compose:
   ```
   docker-compose up -d
   ```

3. The API will be available at http://localhost:8000

### API Endpoints

#### Process a Receipt

```
POST /receipts/process
```

Example request body:
```json
{
  "retailer": "Target",
  "purchaseDate": "2022-01-01",
  "purchaseTime": "13:01",
  "items": [
    {
      "shortDescription": "Mountain Dew 12PK",
      "price": "6.49"
    },
    {
      "shortDescription": "Emils Cheese Pizza",
      "price": "12.25"
    }
  ],
  "total": "18.74"
}
```

Response:
```json
{
  "id": "generated-uuid-from-post-response"
}
```

#### Get Points for a Receipt

```
GET /receipts/{receipt_id}/points
```

Response:
```json
{
  "points": 28
}
```

## Point Calculation Rules

Points are calculated based on the following rules:

1. One point for every alphanumeric character in the retailer name.
2. 50 points if the total is a round dollar amount with no cents.
3. 25 points if the total is a multiple of 0.25.
4. 5 points for every two items on the receipt.
5. If the trimmed length of the item description is a multiple of 3, multiply the price by 0.2 and round up to the nearest integer.
6. 5 points if the total is greater than 10.00.
7. 6 points if the day in the purchase date is odd.
8. 10 points if the time of purchase is after 2:00pm and before 4:00pm.