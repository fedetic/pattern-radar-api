from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow local frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/patterns")
async def get_patterns(pair: str = Query(...)):
    # Example: Replace this with real pattern logic later
    return [
        {"name": "Double Bottom", "category": "Chart", "confidence": 0.94},
        {"name": "Hammer", "category": "Candle", "confidence": 0.89}
    ]


@app.get("/pairs")
async def get_pairs():
    # Example: Replace this with real pattern logic later
    return [
        {
            "symbol": "BTC-USD",
            "base": "BTC",
            "quote": "USD",
            "label": "BTC/USD",
            "status": "active"
        },
        {
            "symbol": "ETH-USD",
            "base": "ETH",
            "quote": "USD",
            "label": "ETH/USD",
            "status": "active"
        },
        {
            "symbol": "SOL-USD",
            "base": "SOL",
            "quote": "USD",
            "label": "SOL/USD",
            "status": "active"
        }
    ]