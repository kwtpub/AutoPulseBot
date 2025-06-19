import asyncio
from app.pipeline import process_all_cars_from_channel

if __name__ == "__main__":
    asyncio.run(process_all_cars_from_channel()) 