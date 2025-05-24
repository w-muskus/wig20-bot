import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
import asyncio

load_dotenv()
bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

async def fetch_wig20():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9"
    }

    # Źródło 1: Stooq API (główne)
    try:
        url = "https://stooq.pl/q/l/?s=wig20&f=sd2t2ohlc&h&e=json"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'symbols' in data and len(data['symbols']) > 0:
            return f"{data['symbols'][0]['close']} PLN"  # Poprawiony dostęp do danych

    except Exception as e:
        print(f"Błąd Stooq API: {e}")

    # Źródło 2: GPW Benchmark (zapasowe)
    try:
        url = "https://gpwbenchmark.pl/karta-indeksu?isin=PL9999999987"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        value_element = soup.find('span', class_='index-value')
        if value_element:
            return f"{value_element.text.strip().replace(' ', '')} pkt"

    except Exception as e:
        print(f"Błąd GPW Benchmark: {e}")

    return "Brak danych"

@tasks.loop(seconds=60)
async def daily_update():
    now = datetime.utcnow()
    target_time = time(6, 0)  # 8:00 czasu polskiego

    if now.time() >= target_time:
        try:
            index_value = await fetch_wig20()
            channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))

            embed = discord.Embed(
                title="📈 Aktualny indeks WIG20",
                description=f"**Wartość:** {index_value}",
                color=0x00ff00
            )
            embed.set_footer(text=f"Aktualizacja: {now.strftime('%Y-%m-%d %H:%M')} UTC")

            await channel.send(embed=embed)
            await asyncio.sleep(86400 - 60)

        except Exception as e:
            print(f"Błąd wysyłki: {e}")

@bot.event
async def on_ready():
    print(f"Bot {bot.user} działa poprawnie!")
    if not daily_update.is_running():
        daily_update.start()

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
