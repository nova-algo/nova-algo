from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import asyncio

from rebalancr.api.websocket import connection_manager
from rebalancr.services.portfolio import PortfolioService
from rebalancr.services.market import MarketService
from rebalancr.strategy.state_rebalancer import StateRebalancer

router = APIRouter()
portfolio_service = PortfolioService()
market_service = MarketService()
rebalancer = StateRebalancer()

# Flag to control the background task
is_portfolio_monitor_running = False

async def monitor_portfolios():
    """Background task to monitor portfolios and trigger rebalancing when needed"""
    global is_portfolio_monitor_running
    is_portfolio_monitor_running = True
    
    while is_portfolio_monitor_running:
        try:
            # Get all active portfolios that need monitoring
            active_portfolios = await portfolio_service.get_active_portfolios()
            
            for portfolio in active_portfolios:
                user_id = portfolio['user_id']
                portfolio_id = portfolio['id']
                
                # Check if portfolio needs rebalancing
                market_data = await market_service.get_latest_data()
                rebalance_needed = await rebalancer.check_rebalance_needed(
                    portfolio_id, 
                    market_data
                )
                
                if rebalance_needed:
                    # Notify user that rebalancing is recommended
                    await connection_manager.send_personal_message(
                        {
                            "type": "rebalance_recommendation",
                            "portfolio_id": portfolio_id,
                            "message": "Market conditions have changed. Rebalancing is recommended."
                        },
                        user_id
                    )
                
                # Send portfolio updates regardless
                portfolio_data = await portfolio_service.get_portfolio(user_id, portfolio_id)
                await connection_manager.send_personal_message(
                    {
                        "type": "portfolio_update",
                        "portfolio_id": portfolio_id,
                        "data": portfolio_data
                    },
                    user_id
                )
                
            # Wait before next check
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            print(f"Error monitoring portfolios: {str(e)}")
            await asyncio.sleep(60)  # Wait and retry

@router.post("/monitor/start")
async def start_portfolio_monitor(background_tasks: BackgroundTasks):
    """Start the portfolio monitoring background task"""
    global is_portfolio_monitor_running
    if not is_portfolio_monitor_running:
        background_tasks.add_task(monitor_portfolios)
        return JSONResponse({"status": "Portfolio monitoring started"})
    return JSONResponse({"status": "Portfolio monitoring already running"})

@router.post("/monitor/stop")
async def stop_portfolio_monitor():
    """Stop the portfolio monitoring background task"""
    global is_portfolio_monitor_running
    is_portfolio_monitor_running = False
    return JSONResponse({"status": "Portfolio monitoring stopped"})

@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: int, user_id: str):
    """Get a specific portfolio"""
    try:
        portfolio = await portfolio_service.get_portfolio(user_id, portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebalance/{portfolio_id}")
async def rebalance_portfolio(portfolio_id: int, user_id: str):
    """Trigger a portfolio rebalance"""
    try:
        # Perform the rebalance operation
        rebalance_result = await rebalancer.rebalance_portfolio(user_id, portfolio_id)
        
        # Notify the user about rebalance results via WebSocket
        await connection_manager.send_personal_message(
            {
                "type": "rebalance_complete",
                "portfolio_id": portfolio_id,
                "data": rebalance_result
            },
            user_id
        )
        
        return rebalance_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
