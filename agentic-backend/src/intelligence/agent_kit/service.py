from coinbase_agentkit import (
    AgentKit, AgentKitConfig, CdpWalletProvider, CdpWalletProviderConfig,
    cdp_api_action_provider, cdp_wallet_action_provider, 
    erc20_action_provider, morpho_action_provider, pyth_action_provider, wallet_action_provider, weth_action_provider, wow_action_provider
)
#from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_deepseek import ChatDeepSeek

from coinbase_agentkit_langchain import get_langchain_tools
from langchain_openai import ChatOpenAI
from rebalancr.execution.providers.kuru.kuru_action_provider import kuru_action_provider
from rebalancr.execution.providers.market_action import market_action_provider
from ...config import Settings
import logging
from rebalancr.execution.providers.rebalancer.rebalancer_action_provider import rebalancer_action_provider

logger = logging.getLogger(__name__)

# Client Layer (business logic)
#     ↓ calls
# Service Layer (send_message)
#     ↓ calls 
# Agent Manager (get_agent_response)
#     ↓ uses
# ReAct Pattern Implementation

class AgentKitService:
    """
    Core service provider for AgentKit functionality.
    Handles initialization, configuration, and provides infrastructure-level operations.
    Implemented as a singleton to ensure consistent access throughout the application.
    """
    _instance = None  # Singleton pattern
    
    @classmethod
    def get_instance(cls, config: Settings, wallet_provider=None, agent_manager=None):
        """Get singleton instance of AgentKitService"""
        if cls._instance is None:
            # Only create a new instance if one doesn't exist
            cls._instance = cls(config, wallet_provider, agent_manager)
        else:
            # Update existing instance with new providers if provided
            if wallet_provider is not None:
                cls._instance.set_wallet_provider(wallet_provider)
            if agent_manager is not None:
                cls._instance.set_agent_manager(agent_manager)
            # Log that we're reusing the existing instance
            logger.debug("Reusing existing AgentKitService instance")
        return cls._instance
    
    def __init__(self, config: Settings, wallet_provider=None, agent_manager=None):
        """Initialize the AgentKit service with necessary providers and configuration."""
        logger.info("Initializing AgentKitService")
        
        # Create context with session information
        context = {
            "user_id": "current_user"  # Default value, will be updated later
        }
        
        # First create Kuru provider
        kuru_provider = kuru_action_provider()
        
        # Create rebalancer provider with minimal dependencies
        # It will be fully configured later
        rebalancer_provider = rebalancer_action_provider(
            wallet_provider=wallet_provider,
            kuru_provider=kuru_provider,
            context=context,
            config=config
        )

        # Store dependencies passed in rather than importing getters
        self.wallet_provider = wallet_provider  # Will be set later if None
        self.agent_manager = agent_manager      # Will be set later if None
        self.context = context
        self.rebalancer_provider = rebalancer_provider  # Store the reference
        
        # Register action providers including rebalancer
        self.agent_kit = AgentKit(AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                erc20_action_provider(),
                pyth_action_provider(),
                weth_action_provider(),
                kuru_provider,
                wallet_action_provider(),
                morpho_action_provider(),
                wow_action_provider(),
                rebalancer_provider,  # Add rebalancer during initialization
            ]
        ))
        
        # For LangChain integration
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL or "gpt-4o-mini",
            api_key=config.OPENAI_API_KEY
        )
        self.tools = get_langchain_tools(self.agent_kit)
        
        # Store configuration
        self.config = config
        
        logger.info("AgentKitService initialized successfully")
        
        # Don't call _complete_initialization here - it will be called when needed
    
    def set_wallet_provider(self, wallet_provider):
        """Set wallet provider after initialization"""
        self.wallet_provider = wallet_provider
        if self.agent_kit:
            self.agent_kit.wallet_provider = wallet_provider
            
    def set_agent_manager(self, agent_manager):
        """Set agent manager after initialization"""
        self.agent_manager = agent_manager
    
    def get_agent_kit(self):
        """Get the shared AgentKit instance"""
        return self.agent_kit

    def _get_base_action_providers(self):
        """Get the base action providers without circular dependencies"""
        return [
            # cdp_api_action_provider(
            #     CdpWalletProviderConfig(

            #     )
            # ),
            # cdp_wallet_action_provider(),
            erc20_action_provider(),
            pyth_action_provider(),
            weth_action_provider(),
            kuru_action_provider(),
            market_action_provider(
                allora_client=None,
                market_analyzer=None,
                market_data_service=None
            ),
            #wallet_action_provider(),
            morpho_action_provider(),
            wow_action_provider(),
            
        ]
        
    def register_portfolio_provider(self, portfolio_provider):
        """Register the portfolio provider after IntelligenceEngine is initialized"""
        self.agent_kit.action_providers.append(portfolio_provider)
        # Update tools for LangChain
        self.tools = get_langchain_tools(self.agent_kit)
        logger.info("Portfolio provider registered successfully")

    def register_rebalancer_provider(self, rebalancer_provider):
        """Register the rebalancer provider after IntelligenceEngine is initialized"""
        # Log provider details
        logger.info(f"Attempting to register rebalancer provider: {rebalancer_provider}")
        logger.info(f"Provider name: {rebalancer_provider.name if hasattr(rebalancer_provider, 'name') else 'unknown'}")
        
        # Check if it's already registered
        for idx, provider in enumerate(self.agent_kit.action_providers):
            provider_name = provider.name if hasattr(provider, 'name') else f"provider_{idx}"
            logger.info(f"Existing provider {idx}: {provider_name}")
            if hasattr(provider, 'name') and provider.name == "rebalancer":
                logger.info("Rebalancer provider already registered")
                return
            
        # Add to action providers
        self.agent_kit.action_providers.append(rebalancer_provider)
        
        # Update tools for LangChain
        self.tools = get_langchain_tools(self.agent_kit)
        
        logger.info("Rebalancer provider registered successfully")
        logger.info(f"Total providers after registration: {len(self.agent_kit.action_providers)}")
        
    def get_action_providers(self):
        """Get the registered action providers."""
        return self.agent_kit.action_providers
        
    async def send_message(self, conversation_id, content):
        """Send a message to an existing conversation."""
        if self.agent_manager:
            return await self.agent_manager.get_agent_response(conversation_id, content)
        else:
            logger.error("Agent manager not set, cannot send message")
            raise RuntimeError("Agent manager not initialized")

    def update_user_context(self, user_id: str):
        """Update the user ID in the context for all providers"""
        if hasattr(self, 'context'):
            self.context["user_id"] = user_id
            
            # Update context in any providers that use it
            for provider in self.agent_kit.action_providers:
                if hasattr(provider, 'context'):
                    provider.context["user_id"] = user_id
            
            logger.info(f"Updated user context to user_id: {user_id}")

    def get_rebalancer_provider(self):
        """Lazily initialize and return the rebalancer provider"""
        if self.rebalancer_provider is None:
            logger.info("Lazily initializing rebalancer provider")
            
            try:
                # Import dependencies only when needed
                from rebalancr.api.dependencies import (
                    get_db_manager, get_intelligence_engine, 
                    get_performance_analyzer, get_strategy_engine, get_trade_reviewer
                )
                
                # Create rebalancer provider
                self.rebalancer_provider = rebalancer_action_provider(
                    wallet_provider=self.wallet_provider,
                    intelligence_engine=get_intelligence_engine(),
                    strategy_engine=get_strategy_engine(),
                    trade_reviewer=get_trade_reviewer(),
                    performance_analyzer=get_performance_analyzer(),
                    db_manager=get_db_manager(),
                    kuru_provider=self.agent_kit.action_providers[3],  # Assuming kuru is at index 3
                    context=self.context,
                    config=self.config
                )
                
                # Register the provider
                self.register_rebalancer_provider(self.rebalancer_provider)
                
            except Exception as e:
                logger.error(f"Error initializing rebalancer provider: {str(e)}")
            
        return self.rebalancer_provider

    def _complete_rebalancer_initialization(self):
        """Complete the rebalancer provider initialization with all required dependencies"""
        if self.rebalancer_provider:
            try:
                # Import dependencies only when needed
                from rebalancr.api.dependencies import (
                    get_db_manager, get_intelligence_engine, 
                    get_performance_analyzer, get_strategy_engine, get_trade_reviewer
                )
                
                # Set dependencies on rebalancer
                self.rebalancer_provider.set_intelligence_engine(get_intelligence_engine())
                self.rebalancer_provider.set_strategy_engine(get_strategy_engine())
                self.rebalancer_provider.set_trade_reviewer(get_trade_reviewer())
                self.rebalancer_provider.set_performance_analyzer(get_performance_analyzer())
                self.rebalancer_provider.set_db_manager(get_db_manager())
                
                # Debug logging to see action methods
                import inspect
                all_methods = inspect.getmembers(self.rebalancer_provider, predicate=inspect.ismethod)
                logger.info(f"Total methods in rebalancer provider: {len(all_methods)}")
                
                # Get action methods 
                action_methods = [name for name, method in all_methods 
                                 if hasattr(method, '_action_decorator_metadata')]
                logger.info(f"Action methods found: {action_methods}")
                
                # Check if provider is already in the list
                provider_in_list = False
                for provider in self.agent_kit.action_providers:
                    if (hasattr(provider, 'name') and provider.name == "rebalancer") or provider is self.rebalancer_provider:
                        provider_in_list = True
                        break
                
                # Add to action_providers if not already there
                if not provider_in_list:
                    logger.info("Adding rebalancer provider to action providers list")
                    self.agent_kit.action_providers.append(self.rebalancer_provider)
                else:
                    logger.info("Rebalancer provider is already in the action providers list")
                
                # SIMPLIFIED: Just regenerate all tools from the main agent_kit
                from coinbase_agentkit_langchain import get_langchain_tools
                self.tools = get_langchain_tools(self.agent_kit)
                
                # Log tool details for debugging
                tool_names = [t.name for t in self.tools]
                logger.info(f"Updated tools list ({len(self.tools)} total): {tool_names}")
                
                # Check specifically for rebalancer tools
                rebalancer_tools = [t for t in self.tools if t.name.startswith('rebalancer')]
                logger.info(f"Found {len(rebalancer_tools)} rebalancer tools: {[t.name for t in rebalancer_tools]}")
                
                logger.info("Rebalancer provider fully initialized with all dependencies")
                
            except Exception as e:
                logger.error(f"Error completing rebalancer initialization: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

    def shutdown(self):
        """Clean up resources during service shutdown"""
        # Clean up rebalancer if needed
        if hasattr(self, 'rebalancer_provider') and self.rebalancer_provider:
            # Call any cleanup methods needed
            pass

