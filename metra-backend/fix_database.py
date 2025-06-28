import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def fix_database():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "")
    
    # Convert postgres:// to postgresql:// if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Create async engine
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Check if column already exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='invite_code_used'
            """))
            
            if result.rowcount == 0:
                # Add the missing column
                print("Adding invite_code_used column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN invite_code_used VARCHAR
                """))
                print("Column added successfully!")
            else:
                print("Column invite_code_used already exists.")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_database()) 