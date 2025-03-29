import asyncio
import logging
import time
from ..database.db_manager import DatabaseManager
from ..strategy.engine import StrategyEngine

logger = logging.getLogger(__name__)

async def monitor_portfolios(db_manager: DatabaseManager, strategy_engine: StrategyEngine, connection_manager=None):
    """Background task to monitor portfolios and trigger rebalancing when needed"""
    # Keep track of last check times
    last_check_times = {}
    
    logger.info("Starting portfolio monitoring service")
    
    while True:
        try:
            # Get all active portfolios
            active_portfolios = await db_manager.get_active_portfolios()
            current_time = time.time()
            
            logger.info(f"Checking {len(active_portfolios)} active portfolios")
            
            for portfolio in active_portfolios:
                user_id = portfolio.get('user_external_id')  # Using external_id from join if available
                if not user_id:
                    user_id = portfolio.get('user_id')
                portfolio_id = portfolio.get('id')
                
                # Check if it's time to analyze this portfolio based on check_interval
                check_interval = portfolio.get("check_interval", 86400)  # Default daily
                last_check = last_check_times.get(portfolio_id, 0)
                
                if current_time - last_check >= check_interval:
                    # Time to check this portfolio
                    last_check_times[portfolio_id] = current_time
                    
                    logger.info(f"Analyzing portfolio {portfolio_id} for user {user_id}")
                    
                    # Check if portfolio needs rebalancing
                    try:
                        analysis = await strategy_engine.analyze_rebalance_opportunity(user_id, portfolio_id)
                        
                        if analysis.get("rebalance_recommended", False):
                            logger.info(f"Rebalance recommended for portfolio {portfolio_id}")
                            
                            # Check if auto-rebalance is enabled for this portfolio
                            # In SQLite, boolean values are stored as integers (0 or 1)
                            if portfolio.get("auto_rebalance", 0) == 1:
                                try:
                                    logger.info(f"Auto-rebalance enabled, executing rebalance for portfolio {portfolio_id}")
                                    
                                    # Execute the rebalance
                                    rebalance_result = await strategy_engine.execute_rebalance(
                                        user_id, 
                                        portfolio_id,
                                        max_slippage=portfolio.get("max_slippage", 1.0)
                                    )
                                    
                                    # Notify user if connection_manager is available
                                    if connection_manager:
                                        await connection_manager.send_personal_message(
                                            {
                                                "type": "rebalance_executed",
                                                "portfolio_id": portfolio_id,
                                                "message": f"Automatic rebalancing executed: {rebalance_result.get('summary', 'Completed')}"
                                            },
                                            user_id
                                        )
                                    
                                    # Log the automatic rebalance
                                    await db_manager.log_portfolio_event(
                                        portfolio_id=portfolio_id,
                                        event_type="auto_rebalance",
                                        details=rebalance_result
                                    )
                                    
                                    logger.info(f"Successfully rebalanced portfolio {portfolio_id}")
                                    
                                except Exception as e:
                                    logger.error(f"Error executing auto-rebalance for portfolio {portfolio_id}: {str(e)}")
                                    
                                    # Notify user of the error if connection_manager is available
                                    if connection_manager:
                                        await connection_manager.send_personal_message(
                                            {
                                                "type": "rebalance_error",
                                                "portfolio_id": portfolio_id,
                                                "message": f"Error during automatic rebalancing: {str(e)}"
                                            },
                                            user_id
                                        )
                            else:
                                logger.info(f"Auto-rebalance not enabled for portfolio {portfolio_id}, sending recommendation")
                                
                                # Just send recommendation if connection_manager is available
                                if connection_manager:
                                    await connection_manager.send_personal_message(
                                        {
                                            "type": "rebalance_recommendation",
                                            "portfolio_id": portfolio_id,
                                            "message": analysis.get("message", "Rebalancing is recommended.")
                                        },
                                        user_id
                                    )
                    except Exception as e:
                        logger.error(f"Error analyzing portfolio {portfolio_id}: {str(e)}")
            
            # Wait before next check
            await asyncio.sleep(60)  # Check every minute, but respect individual portfolio intervals
            
        except Exception as e:
            logger.error(f"Error monitoring portfolios: {str(e)}")
            await asyncio.sleep(60)  # Wait and retry