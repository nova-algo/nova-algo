import sqlite3
import logging
import os
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

def run_migration(db_path):
    """Add columns for auto-rebalancing to portfolios table"""
    try:
        # Make sure we're using the file path, not the URI
        file_path = db_path.replace("sqlite:///", "")
        
        logger.info(f"Running migration on database at {file_path}")
        
        # Connect to the database - we keep this synchronous for simplicity
        # as migrations typically run at startup before async event loop is active
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(portfolios)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add auto_rebalance column if it doesn't exist
        if "auto_rebalance" not in columns:
            cursor.execute("ALTER TABLE portfolios ADD COLUMN auto_rebalance INTEGER DEFAULT 0")
            logger.info("Added auto_rebalance column to portfolios table")
            
        # Add max_slippage column if it doesn't exist
        if "max_slippage" not in columns:
            cursor.execute("ALTER TABLE portfolios ADD COLUMN max_slippage REAL DEFAULT 1.0")
            logger.info("Added max_slippage column to portfolios table")
            
        # Add check_interval column if it doesn't exist
        if "check_interval" not in columns:
            cursor.execute("ALTER TABLE portfolios ADD COLUMN check_interval INTEGER DEFAULT 86400")
            logger.info("Added check_interval column to portfolios table")
            
        # Commit the changes
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error in migration: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

# Add an async version for cases where we need to run migration within async context
async def run_migration_async(db_path):
    """Async wrapper around run_migration for use in async contexts"""
    # Use a thread executor to run the synchronous migration function
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_migration, db_path)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Get the database path from config or use default
    from ..config import Settings
    settings = Settings()
    db_path = settings.DATABASE_URL
    run_migration(db_path)
    
    logger.info("Migration script completed") 