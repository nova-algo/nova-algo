from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import time

from rebalancr.api.websocket import connection_manager
from rebalancr.intelligence.market_data import MarketDataService

router = APIRouter()
market_data_service = MarketDataService()

# Flag to control the background task
is_market_updates_running = False

async def send_market_updates():
    global is_market_updates_running
    is_market_updates_running = True
    
    while is_market_updates_running:
        try:
            # Get latest market data
            market_data = await market_data_service.get_latest_data()
            
            # Broadcast to all connected clients
            await connection_manager.broadcast_to_topic(
                "market_updates", 
                market_data
            )
            
            # Wait before next update
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            print(f"Error sending market updates: {str(e)}")
            await asyncio.sleep(5)  # Wait and retry

@router.post("/market-updates/start")
async def start_market_updates(background_tasks: BackgroundTasks):
    global is_market_updates_running
    if not is_market_updates_running:
        background_tasks.add_task(send_market_updates)
        return JSONResponse({"status": "Market updates started"})
    return JSONResponse({"status": "Market updates already running"})

@router.post("/market-updates/stop")
async def stop_market_updates():
    global is_market_updates_running
    is_market_updates_running = False
    return JSONResponse({"status": "Market updates stopped"}) 