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


async def get_leaderboard(board_type_api):
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
        await asyncio.sleep(2) 
    return []


def format_leaderboard_with_roles(players, my_nicks, time_slot, board_type, guild):
    if not players:
        return None
    payout_data = payouts.get(time_slot, {}).get(board_type, {})
    lines = []    
    for p in players:
        # Гарантируем наличие места (если его нет в объекте p)
        place = p.get('place', '?')
        nick = p['nick_name']
        points = p['points']
        payout = payout_data.get(place, 0)
        if nick in my_nicks:
            role = discord.utils.find(lambda r: r.name == nick, guild.roles)
            # Используем mention только если роль реально существует
            display_nick = role.mention if role else f"**{nick}**"
        else:
            display_nick = nick
        # Компактный формат для Embed, чтобы влезть в лимиты
        line = f"`{place:>2}.` {display_nick} — `{points:.2f}` — **${payout}**"
        lines.append(line)
    # Собираем строки
    result = "\n".join(lines)    
    # Защита от превышения лимита Discord (1024 символа для Field)
    if len(result) > 1000:
        return result[:990] + "..."
    return result



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
    high = await get_leaderboard("high-4hr")
    low = await get_leaderboard("low-4hr")

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

# --- НОВАЯ ФУНКЦИЯ: Единая логика формирования и отправки ---
async def send_leaderboard_logic(destination, guild):
    """
    destination: объект ctx.channel или просто channel
    guild: объект гильдии (нужен для ролей)
    """
    my_nicks_str = os.getenv("MY_NICKNAMES")
    my_nicks = [nick.strip() for nick in my_nicks_str.split(",")] if my_nicks_str else []

    date_str, time_slot = get_utc_date_time_slot()

    # High leaderboard
    high = await get_leaderboard("high-4hr")
    for i, player in enumerate(high, start=1):
        player["place"] = i
    top10 = high[:11]
    top10_names = {p["nick_name"] for p in top10}
    my_outside_top_high = [p for p in high if p["nick_name"] in my_nicks and p["nick_name"] not in top10_names]
    new_high = top10 + my_outside_top_high
    
    # Low leaderboard
    low = await get_leaderboard("low-4hr")
    for i, player in enumerate(low, start=1):
        player["place"] = i
    top15 = low[:16]
    top15_names = {p["nick_name"] for p in top15}
    my_outside_top_low = [p for p in low if p["nick_name"] in my_nicks and p["nick_name"] not in top15_names]
    new_low = top15 + my_outside_top_low

    embed = Embed(
        title=f"🏆 Лидерборд CoinPoker ({time_slot})",
        colour=Colour.from_rgb(30, 144, 255),
        timestamp=datetime.now(timezone.utc)
    )
    try:
        high_text = format_leaderboard_with_roles(new_high, my_nicks, time_slot, "high_leaderboard", guild)
        embed.add_field(name="High leaderboard", value=high_text or "(нет данных)", inline=False)

        low_text = format_leaderboard_with_roles(new_low, my_nicks, time_slot, "low_leaderboard", guild)
        embed.add_field(name="Low leaderboard", value=low_text or "(нет данных)", inline=False)

        if my_nicks:
            embed.set_footer(text="⭐ — ваши участники (выделены цветом роли)")
        
        await destination.send(embed=embed)
    except Exception as e:
        logger.error(f"Ошибка при формировании Embed: {e}")

# --- НОВАЯ ФУНКЦИЯ: Таймер авто-отчета ---
async def schedule_end_of_slot_update(slot_id, guild_id, target_id):
    print(f"DEBUG CONSOLE: Task started for {target_id}") # Это проверим в консоли
    try:
        # Пытаемся получить канал максимально агрессивно
        channel = bot.get_channel(target_id)
        if not channel:
            channel = await bot.fetch_channel(target_id)
        
        await channel.send(f"🛰 [LOG]: Вход в task выполнен. Жду 30 сек...")
        
        await asyncio.sleep(30)
        
        await channel.send("⏳ [LOG]: 30 сек прошло, начинаю fetch гильдии...")
        guild = bot.get_guild(guild_id) or await bot.fetch_guild(guild_id)
        
        await channel.send(f"📡 [LOG]: Гильдия найдена: `{guild.name}`. Запуск logic...")
        await send_leaderboard_logic(channel, guild)

    except Exception as e:
        # Если бот не может отправить в канал, мы увидим это хотя бы в консоли
        print(f"CRITICAL IN TASK: {e}")
        # Попытка отправить в канал еще раз
        try:
            ch = bot.get_channel(target_id) or await bot.fetch_channel(target_id)
            await ch.send(f"‼️ Ошибка внутри таймера: `{e}`")
        except:
            pass

# --- ОБНОВЛЕННАЯ КОМАНДА ---
@bot.command(name="k", aliases=["л", "l", "д"])
async def coloredleaderboard(ctx):
    global last_scheduled_slot, target_channel_id        
    # 1. Сразу выдаем текущий лидерборд
    await send_leaderboard_logic(ctx.channel, ctx.guild)    
    # 2. Логика планирования авто-отчета
    target_channel_id = ctx.channel.id
    date_str, time_slot = get_utc_date_time_slot()
    current_slot_id = f"{date_str}_{time_slot}"       
    #if last_scheduled_slot != current_slot_id:
    last_scheduled_slot = current_slot_id
    await ctx.send(f"🛠 [DEBUG]: Команда принята. ID канала: `{ctx.channel.id}`, ID гильдии: `{ctx.guild.id}`")        
    
    # Создаем задачу и сразу даем ей перехватить цикл
    task = asyncio.create_task(schedule_end_of_slot_update(current_slot_id, ctx.guild.id, ctx.channel.id))
    
    # Проверка: не упала ли задача мгновенно
    await asyncio.sleep(0.5) 
    if task.done() and task.exception():
        await ctx.send(f"❌ [DEBUG]: Задача упала мгновенно: `{task.exception()}`")



# Запуск бота (без изменений)
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("Токен Discord не найден")
        sys.exit(1)
    bot.run(token)


