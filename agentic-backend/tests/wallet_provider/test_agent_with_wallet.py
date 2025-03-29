import asyncio
import logging
import pytest
from ...rebalancr.intelligence.agent_kit.agent_manager import AgentManager
from ...rebalancr.intelligence.agent_kit.service import AgentKitService
from ...rebalancr.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_agent_with_wallet():
    """Test agent with wallet provider integration"""
    logger.info("Starting agent with wallet integration test")
    
    # 1. Initialize settings
    settings = Settings()
    logger.debug("Settings initialized")
    
    # 2. Get service and agent manager instances
    logger.info("Initializing service and agent manager")
    try:
        service = AgentKitService.get_instance(settings)
        agent_manager = AgentManager.get_instance(settings)
        logger.info("Service and agent manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service or agent manager: {str(e)}", exc_info=True)
        raise
    
    # 3. Test user ID
    test_user_id = "test_user_123"
    
    # 4. Create agent with wallet
    logger.info(f"Creating agent for user: {test_user_id}")
    try:
        async with agent_manager.get_agent_executor(test_user_id) as agent:
            logger.info("Agent executor created successfully")
            
            # 5. Test wallet functionality through agent
            logger.info("Querying wallet address through agent")
            wallet_query = await agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": "What is my wallet address?"
                }]
            })
            
            logger.info(f"Agent wallet response: {wallet_query}")
            
            # 6. Try a basic balance query
            logger.info("Querying wallet balance through agent")
            balance_query = await agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": "What is my wallet balance?"
                }]
            })
            
            logger.info(f"Agent balance response: {balance_query}")
    except Exception as e:
        logger.error(f"Error during agent-wallet test: {str(e)}", exc_info=True)
        raise
    
    logger.info("Agent with wallet integration test completed successfully")
    return {
        "success": True,
        "wallet_query": wallet_query,
        "balance_query": balance_query
    }

if __name__ == "__main__":
    logger.info("Running agent with wallet test directly")
    result = asyncio.run(test_agent_with_wallet())
    logger.info(f"Test completed with result: {result}") 