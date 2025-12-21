import asyncio
import requests
import httpx
import time

API_KEY = '596f3686e5d2ad133470311661883510'


def get_weather_sequential(city, api_key):
    """Синхронная функция для получения текущей погоды в выбранном городе
    :param city: выбранный город
    :param api_key: API-ключ OpenWeatherMap"""

    start_time = time.time()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    elapsed_time = time.time() - start_time
    if response.status_code == 200:
        data = response.json()
        return f"Текущая температура в {city}: {data['main']['temp']}°C", data, elapsed_time
    else:
        return f"Ошибка при запросе данных! \n\n{response.text}"


async def get_weather_async(city, api_key):
    """Асинхронная функция для получения текущей погоды в выбранном городе
    :param city: выбранный город
    :param api_key: API-ключ OpenWeatherMap"""

    start_time = time.time()
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}

    async with httpx.AsyncClient(timeout=2) as client:
        response = await client.get(url, params=params)

    elapsed_time = time.time() - start_time
    if response.status_code == 200:
        data = response.json()
        return (
            f"Текущая температура в {city}: {data['main']['temp']}°C",
            data,
            elapsed_time)
    else:
        return f"Ошибка при запросе данных!\n\n{response.text}"


# Вывод: при получении погоды по API асинхронность не ускоряет одиночный запрос.
# Время запроса (синхронная функция): 0.56304 сек
# Время запроса (асинхронная функция): 0.57677 сек
# Скорее всего если бы нужно было в задании реализовать получение погоды для нескольких городов, например 10-20,
# то асинхронная функция работала бы быстрее синхронной.
# Можно провести эксперимент


def experiment_sequential(city, api_key, n=10):
    """Функция для последовательного
     получения погоды n раз для одного города"""
    start = time.time()
    results = []
    for _ in range(n):
        res = get_weather_sequential(city, api_key)
        results.append(res)
    total_time = time.time() - start
    return round(total_time, 5)


async def experiment_async(city, api_key, n=10):
    """Функция для асинхронного
    получения погоды n раз для одного города"""
    start = time.time()
    tasks = [get_weather_async(city, api_key) for i in range(n)]

    results = await asyncio.gather(*tasks)
    total_time = time.time() - start
    return round(total_time, 5)

# Вывод: эксперимент с 10 запросами показал эффективность применения асинхронной функции
# Несколько запросов (синхронная функция): 5.85813 сек
# Несколько запросов (асинхронная функция): 0.68264 сек
# так как время её выполнения равно времени самого долгого запроса
