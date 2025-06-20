import asyncio
from app.pipeline import process_all_cars_from_channel
from app.core.yandex_auth import check_and_refresh_iam_token

async def main():
    # Сначала проверяем и при необходимости обновляем IAM-токен
    await check_and_refresh_iam_token()
    
    # Затем запускаем основной конвейер обработки
    await process_all_cars_from_channel()

if __name__ == "__main__":
    asyncio.run(main()) 