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

    return "




@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")
