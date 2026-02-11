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
    time_slot = f"{start:02d}-{(start + 4):02d}"  # ведущие нули
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
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Команда не найдена. Используйте !help для списка команд.")
    else:
        logger.error(f"Ошибка команды: {error}")

@bot.event
async def on_ready():
    logger.info(f"✅ Бот запущен как {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Бот работает.")

@bot.command(name="l")
@commands.cooldown(1, 30, commands.BucketType.user)
async def leaderboard(ctx):
    try:
        high = get_leaderboard("high-4hr")[:10]
        low = get_leaderboard("low-4hr")[:15]

        if not high and not low:
            await ctx.send("Нет данных для отображения.")
            return

        msg_high = format_leaderboard("🏆 High leaderboard (TOP 10)", high)
        msg_low = format_leaderboard("🥈 Low leaderboard (TOP 15)", low)

        await ctx.send(msg_high + msg_low)

    except Exception as e:
        logger.error(f!Ошибка при выполнении !l: {e}")
        await ctx.send("Ошибка при получении данных. Попробуйте позже.")


if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
