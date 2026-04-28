import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()  # Load .env variables

# Build the DB URL using the same logic as app/db/base.py
url = os.getenv('DATABASE_URL')
if not url:
    user = os.getenv('DATABASE_USER')
    pwd = os.getenv('DATABASE_PASSWORD')
    host = os.getenv('DATABASE_HOST')
    name = os.getenv('DATABASE_NAME')
    url = f'postgresql+asyncpg://{user}:{pwd}@{host}/{name}'

async def main():
    try:
        engine = create_async_engine(url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
        print('✅ Connection succeeded')
    except Exception as exc:
        print('❌ Connection failed')
        print(type(exc).__name__, ':', exc)

if __name__ == '__main__':
    asyncio.run(main())
