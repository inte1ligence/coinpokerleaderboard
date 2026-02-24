import discord
from discord.ext import commands
from discord import (
    Embed,
    Colour,
    utils,
    Role
)
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
import os
import logging
import sys

print("Utils доступен:", hasattr(utils, 'get'))  # Должен вывести True
print(sys.version)
print("Окружение:", os.environ)
print("MY_NICKNAMES:", os.getenv("MY_NICKNAMES"))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
intents = discord.Intents.default()
intents.message_content = True  # ОБЯЗАТЕЛЬНО для !l
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
COINPOKER_URL = "https://coinpoker.com/wp-admin/admin-ajax.php"  # ← Исправьте на "https://..."
last_scheduled_slot = None
target_channel_id = None 
payouts = {
    "00-04": {
        "high_leaderboard": {
            1: 275, 2: 185, 3: 150, 4: 130, 5: 115, 6: 100, 7: 85, 8: 75, 9: 70, 10: 65
        },
        "low_leaderboard": {
            1: 95, 2: 60, 3: 45, 4: 30, 5: 25, 6: 25, 7: 20, 8: 20, 9: 15, 10: 15,
            11: 5, 12: 5, 13: 5, 14: 5, 15: 5
        }
    },
    "04-08": {
        "high_leaderboard": {
            1: 275, 2: 185, 3: 150, 4: 130, 5: 115, 6: 100, 7: 85, 8: 75, 9: 70, 10: 65
        },
        "low_leaderboard": {
            1: 95, 2: 60, 3: 45, 4: 30, 5: 25, 6: 25, 7: 20, 8: 20, 9: 15, 10: 15,
            11: 5, 12: 5, 13: 5, 14: 5, 15: 5
        }
    },
    "08-12": {
        "high_leaderboard": {
            1: 375, 2: 250, 3: 185, 4: 155, 5: 140, 6: 125, 7: 110, 8: 100, 9: 95, 10: 90
        },
        "low_leaderboard": {
            1: 125, 2: 85, 3: 60, 4: 50, 5: 45, 6: 40, 7: 30, 8: 25, 9: 25, 10: 20,
            11: 20, 12: 15, 13: 15, 14: 5, 15: 5
        }
    },
    "12-16": {
        "high_leaderboard": {
            1: 500, 2: 325, 3: 250, 4: 220, 5: 200, 6: 180, 7: 165, 8: 150, 9: 135, 10: 125
        },
        "low_leaderboard": {
            1: 185, 2: 115, 3: 80, 4: 65, 5: 50, 6: 45, 7: 40, 8: 30, 9: 30, 10: 25,
            11: 25, 12: 20, 13: 20, 14: 10, 15: 10
        }
    },
    "16-20": {
        "high_leaderboard": {
            1: 500, 2: 325, 3: 250, 4: 220, 5: 200, 6: 180, 7: 165, 8: 150, 9: 135, 10: 125
        },
        "low_leaderboard": {
            1: 185, 2: 115, 3: 80, 4: 65, 5: 50, 6: 45, 7: 40, 8: 30, 9: 30, 10: 25,
            11: 25, 12: 20, 13: 20, 14: 10, 15: 10
        }
    },
    "20-24": {
        "high_leaderboard": {
            1: 500, 2: 325, 3: 250, 4: 220, 5: 200, 6: 180, 7: 165, 8: 150, 9: 135, 10: 125
        },
        "low_leaderboard": {
            1: 185, 2: 115, 3: 80, 4: 65, 5: 50, 6: 45, 7: 40, 8: 30, 9: 30, 10: 25,
            11: 25, 12: 20, 13: 20, 14: 10, 15: 10
        }
    }
}


def get_utc_date_time_slot():
    now = datetime.now(timezone.utc)  # вместо utcnow()
    date_str = now.strftime("%Y-%m-%d")
    start = (now.hour // 4) * 4
    time_slot = f"{start:02d}-{(start + 4):02d}"
    return date_str, time_slot


def get_leaderboard(board_type_api):
    date_str, time_slot = get_utc_date_time_slot()
    # Сопоставление типов для API и payouts
    board_type_payout = {
        "high-4hr": "high_leaderboard",
        "low-4hr": "low_leaderboard"
    }.get(board_type_api, board_type_api)
    data = {
        "action": "get_current_leaderboard_ajax",
        "date": date_str,
        "time_slot": time_slot,
        "leaderboard": board_type_api
    }
    logger.info(f"Отправляю запрос к API: {data}")
    for attempt in range(3):
        try:
            r = requests.post(COINPOKER_URL, data=data, timeout=20)
            if len(r.content) > 1_000_000:
                logger.error("Ответ API слишком большой (>1 МБ)")
                return []
            if r.status_code == 200:
                content_type = r.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    try:
                        logger.info(f"Получен ответ: {r.text}")
                        return r.json().get("data", {}).get("data", [])
                    except ValueError as e:
                        logger.error(f"Не удалось декодировать JSON: {e}, ответ: {r.text}")
                else:
                    logger.error(f"Ответ не JSON: Content-Type={content_type}, текст: {r.text}")
            else:
                logger.warning(f"Попытка {attempt + 1} API вернул код {r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Попытка {attempt + 1} ошибка сети: {e}, URL: {COINPOKER_URL}, данные: {data}")
        time.sleep(2)
    return []


def format_leaderboard(title, players, my_nicks, time_slot, board_type):
    if not players:
        return f"{title}\n(нет данных)\n"
    payout_data = payouts.get(time_slot, {}).get(board_type, {})
    # Считаем максимальную длину ника С УЧЁТОМ "* "
    max_nick_len = 0
    for p in players:
        nick = p["nick_name"]
        if nick in my_nicks:
            nick = f"{nick}***"
        max_nick_len = max(max_nick_len, len(nick))
    max_points_len = max(len(str(p["points"])) for p in players)
    lines = [title]
    for p in players:
        place = p["place"]
        payout = payout_data.get(place, 0)
        nick_display = p["nick_name"]
        is_my = nick_display in my_nicks
        if is_my:
            nick_display = f"{nick_display}***"
        line = (
            f"{place:>2}. "
            f"{nick_display:<{max_nick_len}}  "
            f"{p['points']:<{max_points_len}}  "
            f"${payout}"
        )
        lines.append(line)
    return "\n".join(lines)


def format_leaderboard_with_roles(players, my_nicks, time_slot, board_type, guild):
    if not players:
        return None
    # ДИАГНОСТИКА: проверяем наличие place у всех игроков
    #missing_place = []
    #for i, p in enumerate(players):
    #    if 'place' not in p:
    #        missing_place.append(f"{i+1}:{p['nick_name']}")
    #if missing_place:
    #   logger.error(f"У игроков отсутствуют поля 'place': {missing_place}")
        # Восстанавливаем place, если его нет
    #    for i, p in enumerate(players, start=1):
    #        if 'place' not in p:
    #            p['place'] = i
    # Сортируем по place для гарантии правильного порядка
    #players = sorted(players, key=lambda x: x['place'])
    payout_data = payouts.get(time_slot, {}).get(board_type, {})
    if not payout_data:
        payout_data = {}
    # Шаг 1: определяем максимальную длину ника (с учётом @)
    max_nick_len = 0
    processed_players = []
    for p in players:
        nick = p['nick_name']
        place = p.get('place', '?') # Берем уже готовый place        
        if nick in my_nicks:
            role = discord.utils.find(lambda r: r.name == nick, guild.roles)
            display_nick = role.mention if role else f"@{nick}"
            # Для отступа используем длину чистого имени, так как mention в Discord 
            # визуально занимает столько же места, сколько текст роли
            calc_len = len(nick) + 1 
        else:
            display_nick = nick
            calc_len = len(nick)
        max_display_len = max(max_display_len, calc_len)
        processed_players.append({
            **p,
            'display_nick': display_nick,
            'calc_len': calc_len,
            'place': place
        })
    # Шаг 2: формируем строки с динамическим отступом
    lines = []
    for p in processed_players:
        place = p['place']
        payout = payout_data.get(place, 0)
        points = p['points']
        display_nick = p['display_nick']
        
        # Динамический отступ (используем разницу длин)
        padding = " " * (max_display_len - p['calc_len'] + 4)
        
        line = (
            f"**{place}.** {display_nick}{padding}"
            f"`{points:>8.2f}`    "
            f"**${payout}**"
        )
        lines.append(line)
    return "\n".join(lines) if lines else None


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

@bot.command(name="debug")
async def debug(ctx):
    date_str, time_slot = get_utc_date_time_slot()
    await ctx.send(
        f"**Текущие параметры запроса:**\n"
        f"- Дата: `{date_str}`\n"
        f"- Тайм-слот: `{time_slot}`\n"
        f"- UTC время: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}`"
    )

@bot.command(name="test_nicks")
async def test_nicks(ctx):
    # 1. Получаем список ваших ников из переменной окружения
    my_nicks_str = os.getenv("MY_NICKNAMES")
    if not my_nicks_str:
        return await ctx.send("❌ Переменная окружения MY_NICKNAMES не задана!")
    
    my_nicks = [nick.strip().lower() for nick in my_nicks_str.split(",")]
    await ctx.send(f"Ваши ники (для проверки): {', '.join(my_nicks)}")

    # 2. Получаем данные лидербордов
    date_str, time_slot = get_utc_date_time_slot()
    high = get_leaderboard("high-4hr")
    low = get_leaderboard("low-4hr")

    # Объединяем оба лидерборда в один список игроков
    all_players = high + low
    api_nicks = {p["nick_name"].lower() for p in all_players}  # Ники из API (нижний регистр)

    # 3. Проверяем, какие ники найдены
    found = []
    not_found = []

    for nick in my_nicks:
        if nick in api_nicks:
            found.append(nick)
        else:
            not_found.append(nick)

    # 4. Формируем ответ
    result = "🔎 Результаты проверки ников:\n"
    
    if found:
        result += f"✅ Найдены в лидерборде: {', '.join(found)}\n"
    else:
        result += "✅ Ники не найдены в текущем лидерборде.\n"
    
    if not_found:
        result += f"❌ Не найдены: {', '.join(not_found)}"
    
    await ctx.send(result)


@bot.command(name="test_api")
async def test_api(ctx):
    try:
        r = requests.get("https://coinpoker.com", timeout=10)
        if r.status_code == 200:
            await ctx.send("✅ API доступно")
        else:
            await ctx.send(f"❌ API вернул код {r.status_code}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка подключения: {e}")



@bot.command(name="l", aliases=["д"])
async def leaderboard(ctx):
    my_nicks_str = os.getenv("MY_NICKNAMES")
    if my_nicks_str:
        my_nicks = [nick.strip() for nick in my_nicks_str.split(",")]
    else:
        my_nicks = []

    date_str, time_slot = get_utc_date_time_slot()

    # High leaderboard
    high = get_leaderboard("high-4hr")
    for i, player in enumerate(high, start=1):
        player["place"] = i
    top10 = high[:11]
    top10_names = {p["nick_name"] for p in top10}
    my_outside_top = [p for p in high if p["nick_name"] in my_nicks and p["nick_name"] not in top10_names]
    new_high = top10 + my_outside_top

    # Low leaderboard
    low = get_leaderboard("low-4hr")
    for i, player in enumerate(low, start=1):
        player["place"] = i
    top15 = low[:16]
    top15_names = {p["nick_name"] for p in top15}
    my_outside_top = [p for p in low if p["nick_name"] in my_nicks and p["nick_name"] not in top15_names]
    new_low = top15 + my_outside_top


    msg = "```\n"
    msg += format_leaderboard(
        "🥇 High leaderboard (TOP 10)",
        new_high,
        my_nicks,
        time_slot=time_slot,
        board_type="high_leaderboard"
    )
    msg += "\n"
    msg += format_leaderboard(
        "🥈 Low leaderboard (TOP 15)",
        new_low,
        my_nicks,
        time_slot=time_slot,
        board_type="low_leaderboard"
    )
    msg += "```"

    if my_nicks:
        msg += (
            "\n⭐ — ваши участники\n"
            "💡 Чтобы выделить цветом ник на сервере: создайте роль с цветом и назначьте её участнику."
        )

    await ctx.send(msg)

@bot.command(name="k", aliases=["л"])
async def coloredleaderboard(ctx):
    my_nicks_str = os.getenv("MY_NICKNAMES")
    if my_nicks_str:
        my_nicks = [nick.strip() for nick in my_nicks_str.split(",")]
    else:
        my_nicks = []
        logger.warning("MY_NICKNAMES не задан в окружении")

    date_str, time_slot = get_utc_date_time_slot()

    # High leaderboard
    high = get_leaderboard("high-4hr")
    # НЕ перезаписываем place — используем данные из API
    top10 = high[:11]
    top10_names = {p["nick_name"] for p in top10}
    my_outside_top = [p for p in high if p["nick_name"] in my_nicks and p["nick_name"] not in top10_names]
    new_high = top10 + my_outside_top
    
    # Low leaderboard
    low = get_leaderboard("low-4hr")
    # НЕ перезаписываем place — используем данные из API
    top15 = low[:16]
    top15_names = {p["nick_name"] for p in top15}
    my_outside_top = [p for p in low if p["nick_name"] in my_nicks and p["nick_name"] not in top15_names]
    new_low = top15 + my_outside_top


    embed = Embed(
        title="🏆 Лидерборд CoinPoker",
        colour=Colour.from_rgb(30, 144, 255),
        timestamp=datetime.now(timezone.utc)
    )

    try:
        # Проверка на пустые данные
        if not new_high:
            high_text = "(нет данных)"
        else:
            high_text = format_leaderboard_with_roles(new_high, my_nicks, time_slot, "high_leaderboard", ctx.guild)
            if not high_text:
                high_text = "(нет данных)"

        embed.add_field(
            name="🥇 High leaderboard (TOP 10)",
            value=high_text,
            inline=False
        )

        if not new_low:
            low_text = "(нет данных)"
        else:
            low_text = format_leaderboard_with_roles(new_low, my_nicks, time_slot, "low_leaderboard", ctx.guild)
            if not low_text:
                low_text = "(нет данных)"

        embed.add_field(
            name="🥈 Low leaderboard (TOP 15)",
            value=low_text,
            inline=False
        )

        if my_nicks:
            embed.set_footer(text="⭐ — ваши участники (выделены цветом роли)")

    except Exception as e:
        logger.error(f"Ошибка при формировании Embed: {e}")
        await ctx.send("Произошла ошибка при формировании лидерборда.")
        return  # Явное завершение команды

    await ctx.send(embed=embed)


    

# Запуск бота
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("Токен Discord не найден в переменной окружения DISCORD_TOKEN")
        sys.exit(1)
    bot.run(token)


