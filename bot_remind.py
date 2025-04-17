from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
import datetime, pytz

scheduler = AsyncIOScheduler()
reminder_jobs = {}  # ใช้เก็บ job ที่ตั้งไว้

async def remind_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_str = context.args[0]
        message = " ".join(context.args[1:]) or "เตือนแล้วจ้า~"

        hour, minute = map(int, time_str.split(":"))
        now = datetime.datetime.now(pytz.timezone("Asia/Bangkok"))
        remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # ถ้าเลยเวลาแล้ว ให้เป็นวันถัดไป
        if remind_time < now:
            remind_time += datetime.timedelta(days=1)

        user_id = update.effective_chat.id
        job_id = f"once-{user_id}-{time_str}-{message}"

        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=remind_time),
            args=[context.application, user_id, message],
            id=job_id
        )

        reminder_jobs[job_id] = f"ครั้งเดียว: {time_str} → {message}"
        await update.message.reply_text(f"📌 เตือนครั้งเดียว: {time_str} → {message}")
    except Exception as e:
        await update.message.reply_text(f"เกิดข้อผิดพลาด: {e}")

async def remind_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        interval = context.args[0]  # เช่น 2h หรือ 30m
        message = " ".join(context.args[1:]) or "เตือนตามรอบแล้วจ้า~"

        if "h" in interval:
            hours = int(interval.replace("h", ""))
            trigger = IntervalTrigger(hours=hours)
        elif "m" in interval:
            minutes = int(interval.replace("m", ""))
            trigger = IntervalTrigger(minutes=minutes)
        else:
            raise ValueError("ใส่รูปแบบระยะเวลาไม่ถูก เช่น 2h หรือ 30m")

        user_id = update.effective_chat.id
        job_id = f"interval-{user_id}-{interval}-{message}"

        scheduler.add_job(
            send_reminder,
            trigger=trigger,
            args=[context.application, user_id, message],
            id=job_id,
            replace_existing=True
        )

        reminder_jobs[job_id] = f"ทุก {interval}: {message}"
        await update.message.reply_text(f"🔁 เตือนทุก {interval}: {message}")
    except Exception as e:
        await update.message.reply_text(f"เกิดข้อผิดพลาด: {e}")

async def remind_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_str = context.args[0]
        message = " ".join(context.args[1:])
        user_id = update.effective_chat.id

        job_id_prefix = f"{user_id}-{time_str}-{message}"
        matched_job_id = next((jid for jid in reminder_jobs if job_id_prefix in jid), None)

        if matched_job_id:
            scheduler.remove_job(matched_job_id)
            del reminder_jobs[matched_job_id]
            await update.message.reply_text(f"❌ ยกเลิกการเตือน: {time_str} → {message}")
        else:
            await update.message.reply_text("ไม่พบการเตือนที่ตรงกับคำสั่งนะ~")
    except Exception as e:
        await update.message.reply_text(f"เกิดข้อผิดพลาด: {e}")

async def remind_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if reminder_jobs:
        text = "📋 รายการแจ้งเตือน:\n" + "\n".join(f"- {v}" for v in reminder_jobs.values())
    else:
        text = "ยังไม่มีการตั้งเตือนน้า~ 💤"
    await update.message.reply_text(text)

async def send_reminder(app, user_id, message):
    await app.bot.send_message(chat_id=user_id, text=f"⏰ ถึงเวลาแล้วนะ! {message}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MookBot พร้อมเตือนทุกแบบแล้วน้าาา ⏰✨")

async def main():
    app = ApplicationBuilder().token("7691645006:AAHC4hDGC8vQEWmqldhT1ntKsjn70PjqrBc").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind_once", remind_once))
    app.add_handler(CommandHandler("remind_interval", remind_interval))
    app.add_handler(CommandHandler("remind_cancel", remind_cancel))
    app.add_handler(CommandHandler("remind_list", remind_list))

    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())