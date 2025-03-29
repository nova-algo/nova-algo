from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
import logging
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from rebalancr.api.dependencies import initialize_services

from rebalancr.tasks.background_tasks import monitor_portfolios

from ..database.db_manager import DatabaseManager
from ..intelligence.agent_kit.wallet_provider import get_wallet_provider

from ..intelligence.allora.client import AlloraClient
from ..chat.history_manager import ChatHistoryManager
from ..websockets.websocket_handlers import handle_websocket
from ..services.market import MarketDataService
from ..strategy.risk_manager import RiskManager
from ..strategy.yield_optimizer import YieldOptimizer
from ..strategy.wormhole import WormholeService
from ..strategy.engine import StrategyEngine
from ..intelligence.intelligence_engine import IntelligenceEngine
from ..intelligence.market_analysis import MarketAnalyzer
from ..intelligence.agent_kit.client import AgentKitClient
from coinbase_agentkit import AgentKit, AgentKitConfig

#from .routes import auth, chat_routes, websocket_routes, wallet_routes
from ..config import get_settings
from ..intelligence.agent_kit.service import AgentKitService
from ..config import Settings
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from .middleware.privy_auth import privy_auth_middleware

import sys

# Configure root logger to show detailed logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
    stream=sys.stderr
)

# Configure logging
logger = logging.getLogger(__name__)

# Load configuration
config = get_settings()

# Initialize application
app = FastAPI(title="Rebalancr API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Privy authentication middleware
app.middleware("http")(privy_auth_middleware)

# Initialize all services
app = initialize_services(app)

#check whether this is correct or if I need to change it to a different endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)

# Include routers
#app.include_router(auth.router)
#app.include_router(chat_routes.router)
#app.include_router(websocket_routes.router, tags=["websocket"])
#app.include_router(wallet_routes.router)


# At the end of your app initialization
@app.on_event("startup")
async def startup_event():
    """Initialize the database and run migrations"""
    await app.state.db_manager.initialize()
    
    # Start portfolio monitoring in background
    background_tasks = BackgroundTasks()
    background_tasks.add_task(
        monitor_portfolios, 
        app.state.db_manager, 
        app.state.strategy_engine
    )
    
    # Initialize all services once at startup
    from .dependencies import initialize_intelligence_services
    initialize_intelligence_services()

    # Get the service
    from rebalancr.api.dependencies import get_agent_kit_service
    service = get_agent_kit_service()
    
    # Log basic info before initialization
    logger.info("STARTUP: Initializing rebalancer provider")
    
    # Complete rebalancer initialization - this already regenerates tools internally
    service._complete_rebalancer_initialization()
    #logger.info(service.tools)
    
    # Just log the tools for verification
    tool_names = [t.name for t in service.tools]
    logger.info(tool_names)
    rebalancer_tools = [name for name in tool_names if name.startswith('rebalancer')]
    
    if rebalancer_tools:
        logger.info(f"Rebalancer tools available: {rebalancer_tools}")
    else:
        logger.warning("No rebalancer tools found with 'rebalancer' prefix")

@app.on_event("shutdown")
async def shutdown_db():
    """Close database connections on shutdown"""
    await app.state.db_manager.close()
# # # Auth dependency - simplified for hackathon
# # async def get_user_from_token(token: str = Query(...)):
# #     # In a real app, validate the token against your database
# #     # For hackathon, just extract user_id from token directly
# #     return token

# # Initialize chat history manager
# chat_history_manager = ChatHistoryManager(db_manager=db_manager)

# # Include all routers
# # app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
# # app.include_router(market.router, prefix="/api/market", tags=["Market"])
# # app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
# # app.include_router(user.router, prefix="/api/user", tags=["User"])
# # app.include_router(social.router, prefix="/api/social", tags=["Social"])
# # app.include_router(achievement.router, prefix="/api/achievement", tags=["Achievement"])

# # WebSocket handler

# # Initialize WebSocket handler
# chat_ws_handler = ChatWebSocketHandler(
#     # strategy_engine=strategy_engine,
#     # agent_kit_client=agent_kit_client
#     portfolio_agent=portfolio_agent,
#     chat_history_manager=chat_history_manager
# )

# # WebSocket Authentication
# async def get_token(
#     websocket: WebSocket,
#     token: Optional[str] = Query(None),
#     authorization: Optional[str] = Header(None)
# ) -> str:
#     # Extract token from Query param or Authorization header
#     if token:
#         return token
#     elif authorization and authorization.startswith("Bearer "):
#         return authorization.replace("Bearer ", "")
#     else:
#         await websocket.close(code=1008)  # Policy violation
#         return None


# # @app.websocket("/ws/chat")
# # async def websocket_chat_endpoint(

# # WebSocket topic subscription handler
# @app.websocket("/ws")
# # async def websocket_endpoint(
# #     websocket: WebSocket, 
# #     #user_id: str = Depends(get_user_from_token)
# #     token: str = Depends(get_token)
# # ):
# #     # Validate token and get user ID
# #     try:
# #         user_id = await user_service.validate_token(token)
# #         if not user_id:
# #             await websocket.close(code=1008)
# #             return
# #     except Exception as e:
# #         print(f"WebSocket authentication error: {str(e)}")
# #         await websocket.close(code=1008)
# #         return

# #     # Accept the connection
# async def websocket_endpoint(websocket: WebSocket):
#     # Accept connection without auth for now
#     user_id = "test_user"  # Hardcoded for testing
    
#     # Accept the connection immediately
#     await connection_manager.connect(websocket, user_id)
    
#     try:
#         ## Handle initial setup message to subscribe to topics
#         # Handle messages
#         while True:
#              # data = await websocket.receive_text()
#             # message_data = json.loads(data)
#             data = await websocket.receive_json()
#               # Process message with chat service
#               #response = await chat_service.process_message(user_id, message_data.get("message", ""))
            
#             message_type = data.get("type", "")
#             print(f"Received message of type: {message_type}")

# #                   # Send response back to this user
# # #             await connection_manager.send_personal_message(
# # #                 {"type": "chat_response", "data": response},
# # #                 user_id
# # #             )
# # #     except WebSocketDisconnect:
# # #         connection_manager.disconnect(websocket, user_id)
# # #         await connection_manager.broadcast(
# # #             {"type": "system", "data": f"User #{user_id} left the chat"}
# # #         )
# # #     except Exception as e:
# # #         print(f"Error in chat websocket: {str(e)}")
# # #         connection_manager.disconnect(websocket, user_id)



@app.get("/")
async def home():
    return {
        "name": "Rebalancr API",
        "status": "online",
        "version": "0.1.0",
        "docs": "/docs"  # Link to FastAPI's automatic docs
    }
