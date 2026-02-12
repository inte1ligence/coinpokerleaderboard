import discord
from discord.ext import commands
import requests
from datetime import datetime
from datetime import timezone
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

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

COINPOKER_URL = "https://coinpoker.com/wp-admin/admin-ajax.php"

def get_utc_date_time_slot():
    now = datetime.now(timezone.utc)  # вместо utcnow()
    date_str = now.strftime("%Y-%m-%d")
    start = (now.hour // 4) * 4
    time_slot = f"{start:02d}-{(start + 4):02d}"
    return date_str, time_slot

def get_leaderboard(board_type):
    date_str, time_slot = get_utc_date_time_slot()
    data = {
        "action": "get_current_leaderboard_ajax",
        "date": date_str,
        "time_slot": time_slot,
        "leaderboard": board_type
    }
    logger.info(f"Отправляю запрос к API: {data}")

    try:
        r = requests.post(COINPOKER_URL, data=data, timeout=15)
        if r.status_code == 200:
            logger.info(f!Получен ответ: {r.text}")
            return r.json().get("data", {}).get("data", [])
        else:
            logger.error(f"API вернул код {r.status_code}: {r.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка API: {e}, URL: {COINPOKER_URL}, данные: {data}")
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

    return "\n" + "\n".join(lines) + "\n"

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Команда не найдена. Используйте !help для списка команд.")
    else:
        logger.error(f"Ошибка команды: {error}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Бот работает.")

@bot.command()
async def status(ctx):
    await ctx.send(
        f"Бот работает!\n"
        f"Версия Python: {sys.version}\n"
        f"Запущен: {bot.user.created_at.strftime('%Y-%m-%d %H:%M')}"
    )

@bot.event
async def on_ready():
    if not hasattr(bot, 'started'):
        bot.started = True
        logger.info(f"✅ Бот запущен как {bot.user}")
    else:
        logger.warning("Повторное подключение — игнорирую.")


@bot.command(name="l")
async def leaderboard(ctx):
    high = get_leaderboard("high-4hr")[:10]
    low = get_leaderboard("low-4hr")[:15]

    msg = ""
    msg += format_leaderboard("🏆 High leaderboard (TOP 10)", high)
    msg += "\n"
    msg += format_leaderboard("🥈 Low leaderboard (TOP 15)", low)

    await ctx.send(msg)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
