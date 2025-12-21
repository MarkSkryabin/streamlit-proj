import requests
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
import time


def get_weather_sequential(city, api_key):
    start_time = time.time()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        elapsed_time = time.time() - start_time
        print(data)
        return f"Погода в {city}: {data['main']['temp']}°C", data, elapsed_time
    else:
        return f"Ошибка при запросе данных! \n\n{response.text}"
