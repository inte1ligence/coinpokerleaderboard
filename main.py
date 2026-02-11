import discord
from discord.ext import commands
import requests
from datetime import datetime
import os
import logging
import sys
print(sys.version)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True  # ОБЯЗАТЕЛЬНО для !l
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

COINPOKER_URL = "https://coinpoker.com/wp-admin/admin-ajax.php"  # Исправлено: https://

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
    try:
        r = requests.post(COINPOKER_URL, data=data, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", {}).get("data", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к API: {e}")
    return []

def format_leaderboard(title, players):
    if not players:
        return f"{title}\n(нет данных)\n"

    # Защита от пустых/некорректных данных
    valid_players = [p for p in players if "nick_name" in p and "points" in p]
    if not valid_players:
        return f"{title}\n(нет данных)\n"

    max_nick_len = max(len(p["nick_name"]) for p in valid_players)
    max_points_len = max(len(str(p["points"])) for p in valid_players)

    lines = [title]
    for i, p in enumerate(valid_players, 1):
        nick = p["nick_name"]
        points = str(p["points"])
        lines.append(f"{i:>2}. {nick:<{max_nick_len}}  {points:<{max_points_len}}")

    return "\n".join(lines) + "\n"


@bot.event
async def on_ready():
    logger.info(f"✅ Бот запущен как {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Бот работает.")

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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Команда не найдена. Используйте !help для списка команд.")
    else:
        logger.error(f"Ошибка команды: {error}")

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
