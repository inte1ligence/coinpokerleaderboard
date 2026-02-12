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


def format_leaderboard(title, players):
    if not players:
        return f"{title}\n(нет данных)\n"

    max_nick_len = max(len(p["nick_name"]) for p in players)
    max_points_len = max(len(str(p["points"])) for p in players)

    lines = [title]
    for i, p in enumerate(players, 1):
        nick = p["nick_name"]
        points = str(p["points"])

        lines.append(
            f"{i:>2}. {nick:<{max_nick_len}}  {points:<{max_points_len}}"
        )

    return "\n".join(lines) + "\n"

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Команда не найдена. Используйте !help для списка команд.")
    else:
        logger.error(f"Ошибка команды: {error}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Бот работает.")

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")


@bot.command(name="l")
async def leaderboard(ctx):
    high = get_leaderboard("high-4hr")[:10]
    low = get_leaderboard("low-4hr")[:15]

    msg = ""
    msg += format_leaderboard("🏆 High leaderboard (TOP 10)", high)
    msg += "\n"
    msg += format_leaderboard("🥈 Low leaderboard (TOP 15)", low)

    await ctx.send(msg)

@bot.command()
async def help(ctx):
    await ctx.send(
        "Команды:\n"
        "!l — лидерборды (High/Low)\n"
        "!ping — проверка работы бота"
    )

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
