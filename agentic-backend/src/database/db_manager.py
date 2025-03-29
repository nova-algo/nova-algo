import aiosqlite
import sqlite3  # Keep for type compatibility
from datetime import datetime
import os
from pathlib import Path
import logging
import asyncio

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        # Use the standard path by default
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = data_dir / "rebalancr.db"
        else:
            self.db_path = db_path
            
        logger.info(f"Initializing database at {self.db_path}")
        self._pool = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the database - to be called during app startup"""
        # Create tables
        await self._create_tables()
        
        # Run migration if needed
        db_path_str = str(self.db_path)
        # Properly format for sqlite:/// if needed
        if not db_path_str.startswith("sqlite:///"):
            db_path_str = f"sqlite:///{db_path_str}"
            
        # Use async wrapper for migration
        await self._run_migration_async(db_path_str)
    
    async def _run_migration_async(self, db_path):
        """Run migrations asynchronously to avoid blocking the event loop"""
        from ..database.db_migration import run_migration
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_migration, db_path)
    
    async def _get_connection(self):
        """Get a database connection from the pool with proper locking"""
        async with self._lock:
            if self._pool is None:
                self._pool = await aiosqlite.connect(self.db_path)
                self._pool.row_factory = aiosqlite.Row
        
        return self._pool
    
    async def close(self):
        """Close the connection pool safely"""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
    
    async def _create_tables(self):
        """Create all necessary tables if they don't exist"""
        logger.info("Creating database tables...")
        conn = await self._get_connection()
        
        try:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    username TEXT,
                    wallet_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agent wallets table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    wallet_address TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Agent settings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    settings_json TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Portfolios table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Assets table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER,
                    token_address TEXT,
                    symbol TEXT,
                    amount REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            """)
            
            # Transactions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER,
                    transaction_hash TEXT,
                    transaction_type TEXT,
                    token_address TEXT,
                    amount REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            """)
            
            # Chat history table (with modern schema from the beginning)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    user_id INTEGER,
                    message TEXT,
                    message_type TEXT,  -- "user", "agent", "tool", "system" 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create indices for faster queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_conversation_id 
                ON chat_history(conversation_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_user_id 
                ON chat_history(user_id)
            """)
            
            # Add portfolio events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER,
                    event_type TEXT,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            """)
            
            # Create index for faster queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_portfolio_events_portfolio_id 
                ON portfolio_events(portfolio_id)
            """)
            
            await conn.commit()
            logger.info("Database initialization complete")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise  # Re-raise the exception after logging
    
    # User methods
    async def create_user(self, external_id, username=None):
        """Create a new user"""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                "INSERT INTO users (external_id, username) VALUES (?, ?)",
                (external_id, username)
            )
            await conn.commit()
            
            # Get the ID of the inserted user
            cursor = await conn.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            user_id = row[0]
            
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None  # Return None on failure
    
    async def get_user_by_external_id(self, external_id):
        """Get user by external ID"""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute("SELECT * FROM users WHERE external_id = ?", (external_id,))
            user = await cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"Error getting user by external ID: {str(e)}")
            return None  # Return None on failure

    async def insert_chat_message(self, message_data):
        """Insert a chat message into the database"""
        # Generate conversation_id if not provided
        if not message_data.get("conversation_id"):
            import time
            message_data["conversation_id"] = f"conv_{int(time.time())}_{message_data['user_id']}"
        
        conn = await self._get_connection()
        try:
            # Insert message
            await conn.execute(
                """
                INSERT INTO chat_history 
                (conversation_id, user_id, message, message_type, timestamp) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message_data["conversation_id"],
                    message_data["user_id"],
                    message_data["message"],
                    message_data["message_type"],
                    message_data.get("timestamp", datetime.now().isoformat())
                )
            )
            
            await conn.commit()
            
            # Get the ID of the inserted message
            cursor = await conn.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            message_id = row[0]
            
            # Return message data with ID
            return {
                "id": message_id,
                **message_data
            }
        except Exception as e:
            logger.error(f"Error inserting chat message: {str(e)}")
            # Standardized error handling - return None on failure
            return None

    async def get_chat_messages(self, conversation_id, limit=50):
        """Get messages for a specific conversation"""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM chat_history 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC 
                LIMIT ?
                """, 
                (conversation_id, limit)
            )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting chat messages: {str(e)}")
            return []  # Return empty list on failure

    async def get_user_conversations(self, user_id, limit=10):
        conn = await self._get_connection()
        try:
            # Get distinct conversation IDs with their latest message
            cursor = await conn.execute(
                """
                SELECT 
                    conversation_id,
                    MAX(timestamp) as last_message_time,
                    COUNT(*) as message_count
                FROM chat_history
                WHERE user_id = ? AND conversation_id IS NOT NULL
                GROUP BY conversation_id
                ORDER BY last_message_time DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            
            rows = await cursor.fetchall()
            conversations = []
            
            for row in rows:
                conv_id = row['conversation_id']
                
                # Get the latest message for this conversation
                cursor2 = await conn.execute(
                    """
                    SELECT * FROM chat_history
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (conv_id,)
                )
                
                last_message = await cursor2.fetchone()
                
                if last_message:
                    conversations.append({
                        'conversation_id': conv_id,
                        'last_message': last_message['message'],
                        'last_message_type': last_message['message_type'],
                        'last_message_time': last_message['timestamp'],
                        'message_count': row['message_count']
                    })
                    
            return conversations
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []  # Return empty list on failure

    async def get_active_portfolios(self):
        """Get all active portfolios from the database"""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT 
                    p.id,
                    p.user_id,
                    p.name,
                    p.created_at,
                    COUNT(a.id) as asset_count,
                    SUM(a.amount) as total_assets
                FROM portfolios p
                LEFT JOIN assets a ON p.id = a.portfolio_id
                GROUP BY p.id
                """
            )
            
            rows = await cursor.fetchall()
            portfolios = [dict(row) for row in rows]
            return portfolios
        except Exception as e:
            logger.error(f"Error getting active portfolios: {str(e)}")
            return []

    async def get_portfolios_with_settings(self):
        """Get all portfolios with rebalancing settings and user external IDs"""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute("""
                SELECT 
                    p.*,
                    u.external_id as user_external_id,
                    COUNT(a.id) as asset_count,
                    SUM(a.amount) as total_assets
                FROM portfolios p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN assets a ON p.id = a.portfolio_id
                GROUP BY p.id
            """)
            
            rows = await cursor.fetchall()
            portfolios = [dict(row) for row in rows]
            return portfolios
        except Exception as e:
            logger.error(f"Error getting portfolios with settings: {str(e)}")
            return []

    async def update_portfolio(self, portfolio_id, update_data):
        """Update portfolio settings including auto-rebalance options"""
        conn = await self._get_connection()
        try:
            # Build the SET clause dynamically based on provided fields
            set_clauses = []
            params = []
            
            for key, value in update_data.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            # No fields to update
            if not set_clauses:
                return False
            
            params.append(portfolio_id)  # For the WHERE clause
            
            query = f"UPDATE portfolios SET {', '.join(set_clauses)} WHERE id = ?"
            await conn.execute(query, params)
            await conn.commit()
            
            # Check if any rows were affected by examining changes
            return True  # Simplified for aiosqlite
        except Exception as e:
            logger.error(f"Error updating portfolio {portfolio_id}: {str(e)}")
            return False

    async def log_portfolio_event(self, portfolio_id, event_type, details=None):
        """Log a portfolio event in the database"""
        conn = await self._get_connection()
        try:
            # Convert details to JSON string if it's a dictionary
            details_json = None
            if details:
                import json
                details_json = json.dumps(details)
            
            # Insert the event
            await conn.execute(
                """
                INSERT INTO portfolio_events 
                (portfolio_id, event_type, details, timestamp) 
                VALUES (?, ?, ?, ?)
                """,
                (
                    portfolio_id,
                    event_type,
                    details_json,
                    datetime.now().isoformat()
                )
            )
            
            # Get the ID of the inserted event
            await conn.commit()
            cursor = await conn.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            event_id = row[0]
            
            return event_id
        except Exception as e:
            logger.error(f"Error logging portfolio event: {str(e)}")
            return None

    async def get_user_portfolios(self, user_id):
        """Get all portfolios for a specific user"""
        conn = await self._get_connection()
        try:
            # Check if user_id is numeric (internal ID) or string (external ID)
            internal_user_id = None
            try:
                internal_user_id = int(user_id)
            except (ValueError, TypeError):
                # If conversion fails, treat as external ID
                user = await self.get_user_by_external_id(user_id)
                if not user:
                    return []
                internal_user_id = user["id"]
            
            # Get portfolios
            cursor = await conn.execute(
                """
                SELECT 
                    p.*,
                    COUNT(a.id) as asset_count,
                    SUM(a.amount) as total_assets
                FROM portfolios p
                LEFT JOIN assets a ON p.id = a.portfolio_id
                WHERE p.user_id = ?
                GROUP BY p.id
                """,
                (internal_user_id,)
            )
            
            # Convert to list of dictionaries
            rows = await cursor.fetchall()
            portfolios = [dict(row) for row in rows]
            return portfolios
        except Exception as e:
            logger.error(f"Error getting user portfolios: {str(e)}")
            return []

    async def get_portfolio(self, portfolio_id):
        """Get a specific portfolio by ID with all its details"""
        conn = await self._get_connection()
        try:
            # Get portfolio with asset statistics
            cursor = await conn.execute(
                """
                SELECT 
                    p.*,
                    u.external_id as user_external_id,
                    COUNT(a.id) as asset_count,
                    SUM(a.amount) as total_assets
                FROM portfolios p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN assets a ON p.id = a.portfolio_id
                WHERE p.id = ?
                GROUP BY p.id
                """,
                (portfolio_id,)
            )
            
            portfolio = await cursor.fetchone()
            
            if not portfolio:
                return None
            
            portfolio_dict = dict(portfolio)
            
            # Get assets for this portfolio
            cursor = await conn.execute(
                """
                SELECT * FROM assets
                WHERE portfolio_id = ?
                """,
                (portfolio_id,)
            )
            
            rows = await cursor.fetchall()
            assets = [dict(row) for row in rows]
            portfolio_dict["assets"] = assets
            
            return portfolio_dict
        except Exception as e:
            logger.error(f"Error getting portfolio: {str(e)}")
            return None

    async def create_conversation(self, user_id):
        """Create a new conversation for a user"""
        try:
            # Generate a unique conversation ID
            import time
            import uuid
            conversation_id = f"conv_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Get internal user ID if needed
            internal_user_id = None
            try:
                internal_user_id = int(user_id)
            except (ValueError, TypeError):
                # If conversion fails, treat as external ID
                user = await self.get_user_by_external_id(user_id)
                if user:
                    internal_user_id = user["id"]
                else:
                    # If no matching user, create a placeholder record
                    internal_user_id = await self.create_user(user_id)
                
            if not internal_user_id:
                logger.error(f"Could not resolve internal ID for user {user_id}")
                return None
            
            # Since conversations are implicit in our schema,
            # we just need to return the generated ID
            return conversation_id
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return None

    async def get_portfolio_events(self, portfolio_id, event_type=None, limit=50):
        """Get events for a specific portfolio"""
        conn = await self._get_connection()
        try:
            # Build query based on whether event_type is provided
            if event_type:
                cursor = await conn.execute(
                    """
                    SELECT * FROM portfolio_events
                    WHERE portfolio_id = ? AND event_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (portfolio_id, event_type, limit)
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT * FROM portfolio_events
                    WHERE portfolio_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (portfolio_id, limit)
                )
            
            rows = await cursor.fetchall()
            events = []
            
            for row in rows:
                event = dict(row)
                
                # Parse JSON details if present
                if event.get('details'):
                    import json
                    try:
                        event['details'] = json.loads(event['details'])
                    except:
                        pass  # Keep as string if parsing fails
                            
                events.append(event)
                
            return events
        except Exception as e:
            logger.error(f"Error getting portfolio events: {str(e)}")
            return []
