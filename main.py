import discord
from discord.ext import commands
import requests
from datetime import datetime, timezone
import os
import logging
import sys

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
            nick = f"* {nick}"
        max_nick_len = max(max_nick_len, len(nick))

    max_points_len = max(len(str(p["points"])) for p in players)


    lines = [title]

    for p in players:
        place = p["place"]
        payout = payout_data.get(place, 0)

        nick_display = p["nick_name"]
        is_my = nick_display in my_nicks
        if is_my:
            nick_display = f"* {nick_display}"

        line = (
            f"{place:>2}. "
            f"{nick_display:<{max_nick_len}}  "
            f"{p['points']:<{max_points_len}}  "
            f"${payout}"
        )

        if is_my:
            line = f"**{line}**"

        lines.append(line)

    return "\n".join(lines)

def format_leaderboard_colored(title: str, players: list, my_nicks: list, time_slot: str, board_type: str, guild: discord.Guild) -> str:
    if not players:
        return f"{title}\n(нет данных)\n"

    payout_data = payouts.get(time_slot, {}).get(board_type, {})
    lines = [f"**{title}**"]

    for p in players:
        place = p["place"]
        nick = p["nick_name"]
        points = round(p["points"], 2)
        payout = round(payout_data.get(place, 0), 2)

        # Ищем участника по нику или отображаемому имени
        member = (
            utils.get(guild.members, nickname=nick) or
            utils.get(guild.members, display_name=nick)
        )

        if member and nick.lower() in [mn.lower() for mn in my_nicks]:
            # Упоминаем участника — Discord сам окрасит ник в цвет роли
            nick_display = member.mention
        else:
            # Обычный текст (не упоминается)
            nick_display = nick

        # Форматируем строку
        line = f"{place:>2}. {nick_display} | {points} pts | ${payout}"
        lines.append(line)

    return "\n".join(lines)


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
    top10 = high[:10]
    top10_names = {p["nick_name"] for p in top10}
    my_outside_top = [p for p in high if p["nick_name"] in my_nicks and p["nick_name"] not in top10_names]
    new_high = top10 + my_outside_top

    # Low leaderboard
    low = get_leaderboard("low-4hr")
    for i, player in enumerate(low, start=1):
        player["place"] = i
    top15 = low[:15]
    top15_names = {p["nick_name"] for p in top15}
    my_outside_top = [p for p in low if p["nick_name"] in my_nicks and p["nick_name"] not in top15_names]
    new_low = top15 + my_outside_top


    msg = "```\n"
    msg += format_leaderboard(
        "🏆 High leaderboard (TOP 10)",
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
async def colored_leaderboard(ctx):
    my_nicks_str = os.getenv("MY_NICKNAMES")
    my_nicks = [nick.strip() for nick in my_nicks_str.split(",")] if my_nicks_str else []

    date_str, time_slot = get_utc_date_time_slot()

    # Получаем данные
    high = get_leaderboard("high-4hr")
    low = get_leaderboard("low-4hr")

    # Назначаем места
    for i, player in enumerate(high, start=1):
        player["place"] = i
    for i, player in enumerate(low, start=1):
        player["place"] = i

    # Топ-10 High + «свои» вне топа
    top10 = high[:10]
    top10_names = {p["nick_name"] for p in top10}
    my_outside_high = [p for p in high if p["nick_name"] in my_nicks and p["nick_name"] not in top10_names]
    display_high = top10 + my_outside_high

    # Топ-15 Low + «свои» вне топа
    top15 = low[:15]
    top15_names = {p["nick_name"] for p in top15}
    my_outside_low = [p for p in low if p["nick_name"] in my_nicks and p["nick_name"] not in top15_names]
    display_low = top15 + my_outside_low

    # Формируем текст с цветными никами
    try:
        high_text = format_leaderboard_colored(
            "🏆 High leaderboard (TOP 10)",
            display_high,
            my_nicks,
            time_slot,
            "high_leaderboard",
            ctx.guild
        )
        low_text = format_leaderboard_colored(
            "🥈 Low leaderboard (TOP 15)",
            display_low,
            my_nicks,
            time_slot,
            "low_leaderboard",
            ctx.guild
        )
    except Exception as e:
        logger.error(f"Ошибка при форматировании цветного лидерборда: {e}")
        await ctx.send("Произошла ошибка при формировании цветного лидерборда.")
        return

    # Собираем сообщение
    msg = f"{high_text}\n\n{low_text}"

    if my_nicks:
        msg += (
            "\n\n⭐ — ваши участники выделены цветом их роли на сервере.\n"
            "💡 Чтобы ник окрасился: создайте роль с цветом и назначьте её участнику."
        )

    # Проверка длины (максимум 2000 символов для простого текста в Discord)
    if len(msg) > 1900:
        await ctx.send("Лидерборд слишком длинный. Используйте `!l` для краткой версии.")
        return

    await ctx.send(msg)

    

# Запуск бота
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("Токен Discord не найден в переменной окружения DISCORD_TOKEN")
        sys.exit(1)
    bot.run(token)


