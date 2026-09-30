import logging
import sqlite3
import random
import json
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"   # <-- Replace this
DB_PATH = "words.db"
DEFAULT_TZ = "Africa/Lagos"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# WORD DATABASE (No external API — built-in)
# ============================================================
WORDS = [
    {"word": "Ephemeral", "pos": "adjective", "meaning": "Lasting for a very short time.",
     "example": "The beauty of the sunset was ephemeral, fading within minutes."},
    {"word": "Serendipity", "pos": "noun", "meaning": "Finding something good without looking for it.",
     "example": "Meeting my best friend on a random train was pure serendipity."},
    {"word": "Eloquent", "pos": "adjective", "meaning": "Fluent and persuasive in speaking or writing.",
     "example": "Her eloquent speech moved the entire audience to tears."},
    {"word": "Resilient", "pos": "adjective", "meaning": "Able to recover quickly from difficulties.",
     "example": "Children are remarkably resilient after setbacks."},
    {"word": "Meticulous", "pos": "adjective", "meaning": "Showing great attention to detail.",
     "example": "He kept meticulous records of every expense."},
    {"word": "Ambiguous", "pos": "adjective", "meaning": "Open to more than one interpretation.",
     "example": "His answer was ambiguous, leaving us all confused."},
    {"word": "Tenacious", "pos": "adjective", "meaning": "Holding firmly to something; persistent.",
     "example": "She was tenacious in pursuit of her goals."},
    {"word": "Pragmatic", "pos": "adjective", "meaning": "Dealing with things sensibly and realistically.",
     "example": "We need a pragmatic approach to solve this problem."},
    {"word": "Candid", "pos": "adjective", "meaning": "Truthful and straightforward; frank.",
     "example": "She gave a candid review of the book."},
    {"word": "Empathy", "pos": "noun", "meaning": "The ability to understand another's feelings.",
     "example": "Great leaders lead with empathy."},
    {"word": "Ubiquitous", "pos": "adjective", "meaning": "Present everywhere at once.",
     "example": "Smartphones have become ubiquitous in modern life."},
    {"word": "Pinnacle", "pos": "noun", "meaning": "The highest point of achievement.",
     "example": "Winning the gold was the pinnacle of his career."},
    {"word": "Nostalgia", "pos": "noun", "meaning": "A sentimental longing for the past.",
     "example": "Old songs fill me with nostalgia."},
    {"word": "Lucid", "pos": "adjective", "meaning": "Expressed clearly; easy to understand.",
     "example": "Her lucid explanation made physics simple."},
    {"word": "Integrity", "pos": "noun", "meaning": "The quality of being honest and having strong morals.",
     "example": "He is a man of great integrity."},
    {"word": "Vivid", "pos": "adjective", "meaning": "Producing powerful, clear images in the mind.",
     "example": "She gave a vivid description of the storm."},
    {"word": "Benevolent", "pos": "adjective", "meaning": "Kind and generous.",
     "example": "A benevolent stranger paid for my meal."},
    {"word": "Frugal", "pos": "adjective", "meaning": "Careful with money; economical.",
     "example": "They lived a frugal life to save for a house."},
    {"word": "Inevitable", "pos": "adjective", "meaning": "Certain to happen; unavoidable.",
     "example": "Change is inevitable in life."},
    {"word": "Curious", "pos": "adjective", "meaning": "Eager to know or learn something.",
     "example": "A curious mind asks great questions."},
    {"word": "Articulate", "pos": "adjective", "meaning": "Able to express ideas clearly.",
     "example": "He is articulate and confident on stage."},
    {"word": "Diligent", "pos": "adjective", "meaning": "Showing care and effort in work.",
     "example": "She is a diligent student who never misses class."},
    {"word": "Insightful", "pos": "adjective", "meaning": "Showing deep understanding.",
     "example": "That was an insightful observation."},
    {"word": "Cordial", "pos": "adjective", "meaning": "Warm and friendly.",
     "example": "They shared a cordial relationship."},
    {"word": "Profound", "pos": "adjective", "meaning": "Very great or intense; deep.",
     "example": "The book had a profound impact on me."},
    {"word": "Zealous", "pos": "adjective", "meaning": "Showing great energy for a cause.",
     "example": "She is a zealous supporter of education."},
    {"word": "Sagacious", "pos": "adjective", "meaning": "Having keen judgment; wise.",
     "example": "The sagacious leader predicted the crisis."},
    {"word": "Prudent", "pos": "adjective", "meaning": "Acting with care and thought for the future.",
     "example": "It was prudent to save for emergencies."},
    {"word": "Dynamic", "pos": "adjective", "meaning": "Full of energy and new ideas.",
     "example": "She has a dynamic personality."},
    {"word": "Vibrant", "pos": "adjective", "meaning": "Full of energy and life.",
     "example": "The city has a vibrant nightlife."},
    {"word": "Coherent", "pos": "adjective", "meaning": "Logical and consistent.",
     "example": "He gave a coherent argument."},
    {"word": "Fervent", "pos": "adjective", "meaning": "Having intense passion.",
     "example": "She made a fervent plea for help."},
    {"word": "Genuine", "pos": "adjective", "meaning": "Truly what it is said to be; sincere.",
     "example": "He showed genuine concern for others."},
    {"word": "Innovative", "pos": "adjective", "meaning": "Introducing new ideas; original.",
     "example": "Their innovative design won the award."},
    {"word": "Concise", "pos": "adjective", "meaning": "Giving a lot of information in few words.",
     "example": "Please keep your answer concise."},
    {"word": "Adaptable", "pos": "adjective", "meaning": "Able to adjust to new conditions.",
     "example": "Adaptable workers thrive in change."},
    {"word": "Astute", "pos": "adjective", "meaning": "Sharp-minded; clever.",
     "example": "An astute investor spots opportunities early."},
    {"word": "Compassionate", "pos": "adjective", "meaning": "Showing sympathy and concern.",
     "example": "She is a compassionate nurse."},
    {"word": "Determined", "pos": "adjective", "meaning": "Firmly decided; resolute.",
     "example": "He was determined to finish the race."},
    {"word": "Earnest", "pos": "adjective", "meaning": "Sincere and serious.",
     "example": "She made an earnest effort to improve."},
    {"word": "Graceful", "pos": "adjective", "meaning": "Showing elegance and smoothness.",
     "example": "The dancer's graceful moves amazed everyone."},
    {"word": "Humble", "pos": "adjective", "meaning": "Not proud; modest.",
     "example": "Despite his success, he remained humble."},
    {"word": "Impartial", "pos": "adjective", "meaning": "Fair and not biased.",
     "example": "A judge must remain impartial."},
    {"word": "Keen", "pos": "adjective", "meaning": "Highly developed; eager.",
     "example": "She has a keen sense of humor."},
    {"word": "Luminous", "pos": "adjective", "meaning": "Giving off light; bright.",
     "example": "The luminous moon lit the path."},
    {"word": "Mindful", "pos": "adjective", "meaning": "Conscious or aware of something.",
     "example": "Be mindful of your words."},
    {"word": "Nurturing", "pos": "adjective", "meaning": "Caring for and encouraging growth.",
     "example": "She has a nurturing personality."},
    {"word": "Optimistic", "pos": "adjective", "meaning": "Hopeful about the future.",
     "example": "He stayed optimistic despite the setback."},
    {"word": "Poised", "pos": "adjective", "meaning": "Calm and confident.",
     "example": "She remained poised under pressure."},
    {"word": "Quintessential", "pos": "adjective", "meaning": "Representing the most perfect example.",
     "example": "He is the quintessential gentleman."},
]

# ============================================================
# DATABASE
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            timezone TEXT DEFAULT 'Africa/Lagos',
            daily_time TEXT DEFAULT '08:00',
            quiz_enabled INTEGER DEFAULT 1,
            joined_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            word TEXT,
            correct INTEGER,
            sent_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_quiz_date TEXT,
            total_correct INTEGER DEFAULT 0,
            total_attempted INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def register_user(user):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, first_name, joined_at) VALUES (?,?,?,?)",
            (user.id, user.username or "", user.first_name or "", datetime.utcnow().isoformat()),
        )
        cur.execute("INSERT OR IGNORE INTO progress (user_id) VALUES (?)", (user.id,))
        conn.commit()
    conn.close()

def get_user(user_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT timezone, daily_time, quiz_enabled FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_user(user_id, field, value):
    if field not in ("timezone", "daily_time", "quiz_enabled"):
        return
    conn = db()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()

def get_progress(user_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT streak, last_quiz_date, total_correct, total_attempted FROM progress WHERE user_id=?",
                (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_progress(user_id, correct: bool):
    conn = db()
    cur = conn.cursor()
    today = datetime.utcnow().date().isoformat()
    cur.execute("SELECT streak, last_quiz_date, total_correct, total_attempted FROM progress WHERE user_id=?",
                (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO progress (user_id) VALUES (?)", (user_id,))
        row = (0, None, 0, 0)

    streak, last_date, total_c, total_a = row
    if correct:
        total_c += 1
        if last_date != today:
            streak += 1
    total_a += 1

    cur.execute(
        "UPDATE progress SET streak=?, last_quiz_date=?, total_correct=?, total_attempted=? WHERE user_id=?",
        (streak, today, total_c, total_a, user_id),
    )
    conn.commit()
    conn.close()

def log_word(user_id, word, correct):
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO history (user_id, word, correct, sent_at) VALUES (?,?,?,?)",
                (user_id, word, 1 if correct else 0, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def all_users():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, timezone, daily_time, quiz_enabled FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

# ============================================================
# WORD HELPERS
# ============================================================
def pick_word_for_today(user_id: int) -> dict:
    """Same word for a user all day; rotates daily."""
    day_index = datetime.utcnow().toordinal() + user_id
    return WORDS[day_index % len(WORDS)]

def build_quiz(word_entry: dict) -> tuple:
    correct = word_entry["meaning"]
    pool = [w["meaning"] for w in WORDS if w["word"] != word_entry["word"]]
    distractors = random.sample(pool, 3)
    options = distractors + [correct]
    random.shuffle(options)
    return options, correct

def format_word_message(entry: dict) -> str:
    return (
        f"📖 *Word of the Day*\n\n"
        f"*{entry['word']}*  _({entry['pos']})_\n\n"
        f"💡 *Meaning:* {entry['meaning']}\n\n"
        f"✍️ *Example:*\n_{entry['example']}_"
    )

# ============================================================
# COMMANDS
# ============================================================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)

    welcome = (
        f"👋 *Welcome, {user.first_name}!*\n\n"
        "I'm *WordOfTheDayBot* — your daily vocabulary coach.\n\n"
        "*What I do:*\n"
        "• 📖 Send you a new word every day\n"
        "• 🧠 Quiz you so it sticks\n"
        "• 📊 Track your streak and progress\n\n"
        "*Commands:*\n"
        "/word — Get today's word\n"
        "/quiz — Take today's quiz\n"
        "/random — Random word from the vault\n"
        "/progress — See your stats\n"
        "/settings — Timezone & daily time\n"
        "/help — Show this menu\n\n"
        "Let's grow your vocabulary! 🚀"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)
    # Send today's word right away
    await send_word(update.effective_user.id, ctx.application)


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await start(update, ctx)


async def word_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await send_word(update.effective_user.id, ctx.application)


async def random_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    entry = random.choice(WORDS)
    await update.message.reply_text(format_word_message(entry), parse_mode=ParseMode.MARKDOWN)


async def quiz_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    entry = pick_word_for_today(update.effective_user.id)
    options, correct = build_quiz(entry)
    ctx.user_data["quiz_answer"] = correct
    ctx.user_data["quiz_word"] = entry["word"]

    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"quiz|{opt[:60]}")] for opt in options
    ]
    await update.message.reply_text(
        f"🧠 *Quiz Time!*\n\nWhat does *{entry['word']}* mean?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


async def progress_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    row = get_progress(update.effective_user.id)
    if not row:
        await update.message.reply_text("No progress yet. Try /quiz!")
        return
    streak, _, total_c, total_a = row
    accuracy = (total_c / total_a * 100) if total_a else 0
    msg = (
        f"📊 *Your Progress*\n\n"
        f"🔥 Streak: *{streak} days*\n"
        f"✅ Correct: *{total_c}*\n"
        f"❓ Attempted: *{total_a}*\n"
        f"🎯 Accuracy: *{accuracy:.1f}%*"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def settings_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌍 Timezone", callback_data="set_tz")],
        [InlineKeyboardButton("⏰ Daily word time", callback_data="set_time")],
        [InlineKeyboardButton("🧠 Toggle daily quiz", callback_data="toggle_quiz")],
    ]
    await update.message.reply_text(
        "⚙️ *Settings*\n\nChoose what to update:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


async def quiz_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("quiz|"):
        return
    choice = data.split("|", 1)[1]
    correct = ctx.user_data.get("quiz_answer", "")
    word = ctx.user_data.get("quiz_word", "the word")

    # because we truncated in callback, do startswith match
    is_correct = correct.startswith(choice) or choice.startswith(correct[:60])

    if is_correct:
        update_progress(update.effective_user.id, True)
        log_word(update.effective_user.id, word, True)
        await query.edit_message_text(
            f"✅ *Correct!*\n\n*{word}* means: {correct}",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        update_progress(update.effective_user.id, False)
        log_word(update.effective_user.id, word, False)
        await query.edit_message_text(
            f"❌ *Not quite.*\n\n*{word}* means: {correct}",
            parse_mode=ParseMode.MARKDOWN,
        )


async def settings_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "set_tz":
        ctx.user_data["awaiting"] = "set_tz"
        await query.message.reply_text(
            "Send your timezone like:\n`Africa/Lagos`\n`Europe/London`\n`America/New_York`",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "set_time":
        ctx.user_data["awaiting"] = "set_time"
        await query.message.reply_text(
            "Send daily word time in 24-hour format like `08:00` or `19:30`.",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "toggle_quiz":
        row = get_user(update.effective_user.id)
        if row:
            new_val = 0 if row[2] else 1
            update_user(update.effective_user.id, "quiz_enabled", new_val)
            status = "ON ✅" if new_val else "OFF ❌"
            await query.message.reply_text(f"Daily quiz is now *{status}*.", parse_mode=ParseMode.MARKDOWN)


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    awaiting = ctx.user_data.get("awaiting")
    if not awaiting:
        return
    text = update.message.text.strip()
    uid = update.effective_user.id

    if awaiting == "set_tz":
        try:
            ZoneInfo(text)
        except Exception:
            await update.message.reply_text("❌ Invalid timezone. Try `Africa/Lagos`.", parse_mode=ParseMode.MARKDOWN)
            return
        update_user(uid, "timezone", text)
        await update.message.reply_text(f"✅ Timezone set to *{text}*", parse_mode=ParseMode.MARKDOWN)
    elif awaiting == "set_time":
        try:
            datetime.strptime(text, "%H:%M")
        except ValueError:
            await update.message.reply_text("❌ Use 24h format like `08:00`.", parse_mode=ParseMode.MARKDOWN)
            return
        update_user(uid, "daily_time", text)
        await update.message.reply_text(f"✅ Daily time set to *{text}*", parse_mode=ParseMode.MARKDOWN)

    ctx.user_data["awaiting"] = None
    schedule_user_jobs(ctx.application, uid)


# ============================================================
# DAILY SENDER
# ============================================================
async def send_word(user_id: int, app: Application):
    entry = pick_word_for_today(user_id)
    try:
        await app.bot.send_message(
            user_id, format_word_message(entry), parse_mode=ParseMode.MARKDOWN
        )
        row = get_user(user_id)
        if row and row[2]:  # quiz_enabled
            options, correct = build_quiz(entry)
            keyboard = [
                [InlineKeyboardButton(opt, callback_data=f"quiz|{opt[:60]}")] for opt in options
            ]
            await app.bot.send_message(
                user_id,
                f"🧠 *Quick Quiz:* What does *{entry['word']}* mean?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN,
            )
    except Exception as e:
        logger.warning(f"Failed to send word to {user_id}: {e}")


async def daily_job(app: Application, user_id: int):
    await send_word(user_id, app)


def schedule_user_jobs(app: Application, user_id: int):
    row = get_user(user_id)
    if not row:
        return
    tz_name, daily_time, _ = row
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo(DEFAULT_TZ)

    scheduler: AsyncIOScheduler = app.bot_data["scheduler"]
    jid = f"{user_id}_daily"
    if scheduler.get_job(jid):
        scheduler.remove_job(jid)

    h, m = map(int, daily_time.split(":"))
    scheduler.add_job(
        daily_job, "cron",
        hour=h, minute=m,
        args=[app, user_id],
        id=jid, replace_existing=True,
        timezone=tz,
    )


async def post_init(app: Application):
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.start()
    app.bot_data["scheduler"] = scheduler
    for (uid, *_rest) in all_users():
        schedule_user_jobs(app, uid)
    logger.info("Scheduler started.")


# ============================================================
# MAIN
# ============================================================
def main():
    init_db()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("word", word_cmd))
    app.add_handler(CommandHandler("random", random_cmd))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("progress", progress_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))

    app.add_handler(CallbackQueryHandler(quiz_callback, pattern="^quiz\\|"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^(set_|toggle_)"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("WordOfTheDayBot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
