import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


API_URL = "https://wttr.in/{city}?format=j1"


class WeatherData:
    def __init__(self, city: str, temperature: float, country: str):
        self.city = city
        self.temperature = temperature
        self.country = country


def load_cities(filename: str) -> list[str]:
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    cities = []

    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            city = line.strip()

            if not city or city.startswith("#"):
                continue

            cities.append(city)

    unique_cities = []
    seen = set()

    for city in cities:
        key = " ".join(city.split()).casefold()

        if key not in seen:
            seen.add(key)
            unique_cities.append(" ".join(city.split()))

    return unique_cities


def get_weather(city: str) -> WeatherData:
    encoded_city = quote(city, safe="")
    url = API_URL.format(city=encoded_city)

    request = Request(
        url,
        headers={
            "User-Agent": "Python Weather"
        }
    )

    with urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    current = data["current_condition"][0]
    area = data["nearest_area"][0]

    temperature = float(current["temp_C"][0] if isinstance(current["temp_C"], list)
                        else current["temp_C"])
    country = area["country"][0]["value"]

    return WeatherData(city, temperature, country)


def format_temperature(value: float) -> str:
    if value.is_integer():
        return f"{int(value):+d}"
    return f"{value:+.1f}"


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "Cities.txt"

    try:
        cities = load_cities(filename)
    except FileNotFoundError as error:
        print(error)
        print("Положите файл со списком городов рядом со скриптом "
              "и назовите его Cities.txt.")
        return

    if not cities:
        print("В файле нет городов.")
        return

    weather_data: list[WeatherData] = []

    print("Получение данных о погоде...")

    for index, city in enumerate(cities):
        try:
            weather = get_weather(city)
            weather_data.append(weather)

            print(
                f"{weather.city}, {weather.country}: "
                f"{format_temperature(weather.temperature)} °C"
            )

        except (HTTPError, URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as error:
            print(f"{city}: не удалось получить данные ({error})")

        if index < len(cities) - 1:
            time.sleep(0.5)

    if not weather_data:
        print("Не удалось получить данные ни для одного города.")
        return

    countries = defaultdict(list)

    for weather in weather_data:
        countries[weather.country].append(weather.temperature)

    print("\nГруппировка по странам:")

    for country in sorted(countries):
        temperatures = countries[country]

        count = len(temperatures)
        average = sum(temperatures) / count
        minimum = min(temperatures)
        maximum = max(temperatures)

        print(
            f"{country} — {count} cities; "
            f"avg: {format_temperature(average)} °C; "
            f"min: {format_temperature(minimum)} °C; "
            f"max: {format_temperature(maximum)} °C"
        )


if __name__ == "__main__":
    main()
