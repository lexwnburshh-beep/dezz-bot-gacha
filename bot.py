import os
import sqlite3
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
DB_PATH = os.getenv("DB_PATH", "dezz_nokos.db")

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL, service TEXT NOT NULL, prefix TEXT NOT NULL,
            demo_number TEXT NOT NULL, claimed_by INTEGER DEFAULT NULL,
            created_at TEXT NOT NULL
        )""")

def is_admin(uid):
    return uid in ADMIN_IDS

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Get Number", callback_data="get")],
        [InlineKeyboardButton("🌍 Change Country", callback_data="countries"),
         InlineKeyboardButton("📱 Change Service", callback_data="services")],
        [InlineKeyboardButton("🔢 Prefix Filter", callback_data="prefix"),
         InlineKeyboardButton("📦 Stock", callback_data="stock")],
        [InlineKeyboardButton("📋 Copy All Numbers", callback_data="copyall")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("country", "Indonesia")
    context.user_data.setdefault("service", "WhatsApp")
    context.user_data.setdefault("prefix", "")
    await update.message.reply_text(
        "👋 Selamat datang di DEZZ NOKOS BOT V1\n\n"
        "Mode DEMO: nomor yang diberikan hanya nomor contoh/fiktif, "
        "bukan nomor aktif dan tidak menerima OTP.\n\n"
        "Pilih menu di bawah:",
        reply_markup=main_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Perintah pengguna:\n/start - Menu utama\n/stock - Lihat stok demo\n\n"
        "Admin:\n/addstock negara|layanan|prefix|jumlah\n"
        "/adminstock - Ringkasan stok"
    )

async def stock_text(country=None, service=None, prefix=None):
    query = "SELECT country, service, prefix, COUNT(*) n FROM stock WHERE claimed_by IS NULL"
    args=[]
    if country:
        query += " AND country=?"; args.append(country)
    if service:
        query += " AND service=?"; args.append(service)
    if prefix:
        query += " AND prefix=?"; args.append(prefix)
    query += " GROUP BY country, service, prefix ORDER BY country, service"
    with db() as con:
        rows=con.execute(query,args).fetchall()
    if not rows:
        return "Stok demo belum tersedia. Admin dapat menambahkan dengan /addstock."
    return "\n".join(f"🌍 {r['country']} | 📱 {r['service']} | prefix {r['prefix']} | stok {r['n']}" for r in rows)

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    country=context.user_data.get("country","Indonesia")
    service=context.user_data.get("service","WhatsApp")
    prefix=context.user_data.get("prefix","")
    if q.data=="get":
        sql="SELECT * FROM stock WHERE claimed_by IS NULL AND country=? AND service=?"
        args=[country,service]
        if prefix:
            sql += " AND prefix=?"; args.append(prefix)
        sql += " ORDER BY id LIMIT 1"
        with db() as con:
            row=con.execute(sql,args).fetchone()
            if row:
                con.execute("UPDATE stock SET claimed_by=? WHERE id=? AND claimed_by IS NULL",(q.from_user.id,row["id"]))
        if not row:
            await q.message.reply_text("Stok demo untuk pilihan ini kosong. Coba ubah negara/layanan atau hubungi admin.")
        else:
            await q.message.reply_text(
                f"📱 Nomor demo kamu: `{row['demo_number']}`\n"
                f"🌍 {row['country']} | {row['service']}\n\n"
                "Nomor ini fiktif dan tidak bisa menerima OTP.",
                parse_mode="Markdown", reply_markup=main_keyboard()
            )
    elif q.data=="countries":
        opts=["Indonesia","Italy","Aruba","United States"]
        await q.message.reply_text("Pilih negara:",reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(x,callback_data="country:"+x)] for x in opts]+
            [[InlineKeyboardButton("⬅️ Menu",callback_data="menu")]]))
    elif q.data.startswith("country:"):
        context.user_data["country"]=q.data.split(":",1)[1]
        await q.message.reply_text("Negara dipilih: "+context.user_data["country"],reply_markup=main_keyboard())
    elif q.data=="services":
        opts=["WhatsApp","Facebook","Telegram","Demo"]
        await q.message.reply_text("Pilih layanan:",reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(x,callback_data="service:"+x)] for x in opts]+
            [[InlineKeyboardButton("⬅️ Menu",callback_data="menu")]]))
    elif q.data.startswith("service:"):
        context.user_data["service"]=q.data.split(":",1)[1]
        await q.message.reply_text("Layanan dipilih: "+context.user_data["service"],reply_markup=main_keyboard())
    elif q.data=="prefix":
        await q.message.reply_text("Kirim prefix melalui chat, contoh: /prefix 62 atau /prefix reset")
    elif q.data=="stock":
        await q.message.reply_text(await stock_text(country,service,prefix),reply_markup=main_keyboard())
    elif q.data=="copyall":
        with db() as con:
            rows=con.execute("SELECT demo_number FROM stock WHERE claimed_by IS NULL AND country=? AND service=? LIMIT 30",(country,service)).fetchall()
        if not rows:
            await q.message.reply_text("Tidak ada nomor demo yang tersedia.")
        else:
            await q.message.reply_text("Daftar nomor demo (maks. 30):\n"+"\n".join(r["demo_number"] for r in rows))
    elif q.data=="help":
        await q.message.reply_text("Pilih negara dan layanan, lalu tekan Get Number. Semua nomor pada V1 ini hanya data demo.")
    elif q.data=="menu":
        await q.message.reply_text("Menu utama:",reply_markup=main_keyboard())

async def prefix_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan /prefix 62 atau /prefix reset")
        return
    val=context.args[0]
    context.user_data["prefix"]="" if val.lower()=="reset" else val.lstrip("+")
    await update.message.reply_text("Prefix filter: "+(context.user_data["prefix"] or "nonaktif"),reply_markup=main_keyboard())

async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await stock_text())

async def addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Perintah ini khusus admin.")
        return
    raw=" ".join(context.args)
    parts=[p.strip() for p in raw.split("|")]
    if len(parts)!=4 or not parts[3].isdigit() or int(parts[3])<1 or int(parts[3])>500:
        await update.message.reply_text("Format: /addstock negara|layanan|prefix|jumlah\nContoh: /addstock Indonesia|WhatsApp|62|10")
        return
    country,service,pfx,count=parts[0],parts[1],parts[2].lstrip("+"),int(parts[3])
    if not country or not service or not pfx:
        await update.message.reply_text("Semua kolom wajib diisi.")
        return
    with db() as con:
        for i in range(count):
            # Invalid, clearly fictitious demo numbers; not assigned to real subscribers.
            demo=f"+000{pfx}DEMO{i+1:04d}"
            con.execute("INSERT INTO stock(country,service,prefix,demo_number,created_at) VALUES(?,?,?,?,?)",
                        (country,service,pfx,demo,datetime.utcnow().isoformat()))
    await update.message.reply_text(f"Berhasil menambahkan {count} stok DEMO untuk {country} / {service}.")

async def adminstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Perintah ini khusus admin.")
        return
    with db() as con:
        total=con.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
        available=con.execute("SELECT COUNT(*) FROM stock WHERE claimed_by IS NULL").fetchone()[0]
    await update.message.reply_text(f"Total stok demo: {total}\nTersedia: {available}\nDiambil: {total-available}")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN belum diatur di environment variables.")
    init_db()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help",help_cmd))
    app.add_handler(CommandHandler("stock",stock_cmd))
    app.add_handler(CommandHandler("prefix",prefix_cmd))
    app.add_handler(CommandHandler("addstock",addstock))
    app.add_handler(CommandHandler("adminstock",adminstock))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
