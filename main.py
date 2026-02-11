import discord
from discord.ext import commands
import requests
from datetime import datetime
import os

TOKEN = os.environ.get("TOKEN")  # или впиши строкой для локального теста

intents = discord.Intents.default()
intents.message_content = True  # ОБЯЗАТЕЛЬНО для !l

bot = commands.Bot(command_prefix="!", intents=intents)

COINPOKER_URL = "https://coinpoker.com/wp-admin/admin-ajax.php"


def get_utc_date_time_slot():
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    start = (now.hour // 4) * 4
    time_slot = f"{start}-{start + 4}"
    return date_str, time_slot


def get_leaderboard(board_type):
    date_str, time_slot = get_utc_date_time_slot()
    data = {
        "action": "get_current_leaderboard_ajax",
        "date": date_str,
        "time_slot": time_slot,
        "leaderboard": board_type
    }
    r = requests.post(COINPOKER_URL, data=data, timeout=10)
    if r.status_code == 200:
        return r.json().get("data", {}).get("data", [])
    return []


@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")


@bot.command(name="l")
async def leaderboard(ctx):
    high = get_leaderboard("high-4hr")[:10]
    low = get_leaderboard("low-4hr")[:15]

    msg = "🏆 High leaderboard (TOP 10)**\n"
    for i, p in enumerate(high, 1):
        msg += f"{i}. {p['nick_name']} — {p['points']}\n"

    msg += "\n🥈 Low leaderboard (TOP 15)**\n"
    for i, p in enumerate(low, 1):
        msg += f"{i}. {p['nick_name']} — {p['points']}\n"

    await ctx.send(msg)

print("🚀 Запускаю bot.run()")
bot.run(TOKEN)
