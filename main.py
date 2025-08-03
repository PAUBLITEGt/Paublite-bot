"""
AlphaChecker v6.1 – sin KeyError, sin residuos
"""

import os
import json
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = "8109961796:AAEgs3rB9myYm0slavf2fqp_QrTpHAklgWM"
ADMIN = 7590578210

DB_USERS = "users.json"
DB_STOCK = "stock.json"
DB_KEYS  = "claves.json"

# ---------- helpers ----------
def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return default

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- teclados ----------
def kb_start(uid):
    kb = [
        [InlineKeyboardButton("📖 Comandos", callback_data="cmds")],
        [InlineKeyboardButton("📦 Ver stock", callback_data="stock")],
    ]
    if uid == ADMIN:
        kb.append([InlineKeyboardButton("⚙️ Panel Admin", callback_data="panel")])
    return InlineKeyboardMarkup(kb)

kb_admin = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔐 Crear claves", callback_data="gen")],
    [InlineKeyboardButton("📤 Subir cuentas", callback_data="upload")],
    [InlineKeyboardButton("🛠️ Editar cuenta", callback_data="edit")],
    [InlineKeyboardButton("🗑️ Eliminar cuenta", callback_data="del")],
    [InlineKeyboardButton("👥 Ver usuarios", callback_data="users")],
])

# ---------- /start ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    img = "https://i.imgur.com/Jf1K2HH.png" if uid != ADMIN else "https://i.imgur.com/5KZ2gKL.png"
    texto = (
        "🎉 *AlphaChecker v6.1*\n"
        "📌 Usuario: `/key CLAVE`  |  `/get sitio cant`\n"
        "📌 Admin: menú abajo"
    )
    await ctx.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=img,
        caption=texto,
        parse_mode="Markdown",
        reply_markup=kb_start(uid)
    )

# ---------- /key ----------
async def key_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="Uso: /key CLAVE")
        return
    clave = ctx.args[0].strip()
    claves = load(DB_KEYS, {})
    if clave not in claves:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Clave inválida.")
        return
    plan, maxi = claves[clave]
    uid = str(update.effective_user.id)
    users = load(DB_USERS, {})
    users[uid] = {"plan": plan, "max": maxi, "usados": 0}
    save(DB_USERS, users)
    del claves[clave]
    save(DB_KEYS, claves)
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ {plan} activado. Accesos: {maxi}")

# ---------- /get ----------
async def get_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="Uso: /get sitio cantidad")
        return
    sitio, cant = ctx.args[0], ctx.args[1]
    try:
        cant = int(cant)
    except ValueError:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="Cantidad debe ser número.")
        return

    uid = str(update.effective_user.id)
    users = load(DB_USERS, {})
    # asegura campos
    reg = users.setdefault(uid, {"plan": "Sin plan", "max": 0, "usados": 0})
    if "usados" not in reg:
        reg["usados"] = 0

    if reg["plan"] == "Sin plan":
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Sin plan activo.")
        return
    disp = reg["max"] - reg["usados"]
    if cant > disp:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Te quedan {disp} accesos.")
        return

    stock = load(DB_STOCK, {})
    if sitio not in stock or len(stock[sitio]) < cant:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Sin stock suficiente.")
        return

    cuentas = stock[sitio][:cant]
    stock[sitio] = stock[sitio][cant:]
    save(DB_STOCK, stock)

    reg["usados"] += cant
    save(DB_USERS, users)

    texto = "\n".join([f"`{c}`" for c in cuentas])
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎁 *{sitio}* ×{cant}\n\n{texto}\n\nUsados: {reg['usados']}/{reg['max']}",
        parse_mode="Markdown"
    )

# ---------- /users ----------
async def users_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ No autorizado.")
        return
    users = load(DB_USERS, {})
    if not users:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="Sin usuarios.")
        return
    lines = [
        f"@{ctx.bot.get_chat(int(uid)).username or uid} – {d['plan']} ({d['usados']}/{d['max']})"
        for uid, d in users.items()
    ]
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👥 *Usuarios:*\n" + "\n".join(lines),
        parse_mode="Markdown"
    )

# ---------- /gen ----------
async def gen_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ No autorizado.")
        return
    claves = {}
    for usos, nombre in [(1, "Bronce 1"), (2, "Plata 2"),
                         (3, "Oro 3"), (4, "Diamante 4")]:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=22))
        claves[key] = (nombre, usos)
    save(DB_KEYS, claves)
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎲 *Claves generadas:*\n" + "\n".join([f"`{k}` → {n}`" for k, (n, _) in claves.items()]),
        parse_mode="Markdown"
    )

# ---------- /upload ----------
async def upload_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ No autorizado.")
        return
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text="📤 Envía: `sitio|correo:clave`")

async def receive_upload(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    lineas = update.message.text.strip().splitlines()
    stock = load(DB_STOCK, {})
    for ln in lineas:
        if "|" not in ln:
            continue
        sitio, cred = ln.split("|", 1)
        sitio, cred = sitio.strip(), cred.strip()
        if sitio and cred:
            stock.setdefault(sitio, []).append(cred)
    save(DB_STOCK, stock)
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text="✅ Cuentas guardadas.")

# ---------- /edit ----------
async def edit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ No autorizado.")
        return
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text="🛠️ Envía: `sitio|índice|correo:clave`")

async def receive_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    texto = update.message.text.strip()
    try:
        sitio, idx_str, nuevo = texto.split("|", 2)
        sitio, idx, nuevo = sitio.strip(), int(idx_str.strip()) - 1, nuevo.strip()
    except ValueError:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Formato incorrecto.")
        return
    stock = load(DB_STOCK, {})
    if sitio not in stock or idx < 0 or idx >= len(stock[sitio]):
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Índice o sitio inválido.")
        return
    stock[sitio][idx] = nuevo
    save(DB_STOCK, stock)
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text="✅ Cuenta actualizada.")

# ---------- /del ----------
async def del_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ No autorizado.")
        return
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text="🗑️ Envía solo el número de la cuenta a eliminar (empieza en 1).\nEjemplo: 3")

async def receive_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    texto = update.message.text.strip()
    try:
        idx = int(texto) - 1
    except ValueError:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Solo envía un número.")
        return

    stock = load(DB_STOCK, {})
    lista = [(sitio, cuenta) for sitio, cuentas in stock.items() for cuenta in cuentas]
    if idx < 0 or idx >= len(lista):
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text="❌ Número no existe.")
        return

    sitio, cuenta = lista[idx]
    stock[sitio].pop(stock[sitio].index(cuenta))
    if not stock[sitio]:
        del stock[sitio]
    save(DB_STOCK, stock)
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Eliminada la cuenta **#{idx+1}**:\n`{cuenta}`",
        parse_mode="Markdown"
    )

# ---------- callbacks ----------
async def callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "panel":
        await query.message.reply_text("⚙️ Panel Admin", reply_markup=kb_admin)
    elif data == "gen":
        await gen_cmd(update, ctx)
    elif data == "upload":
        await upload_cmd(update, ctx)
    elif data == "edit":
        await edit_cmd(update, ctx)
    elif data == "del":
        await del_cmd(update, ctx)
    elif data == "users":
        await users_cmd(update, ctx)
    elif data == "stock":
        stock = load(DB_STOCK, {})
        lineas = [f"*{s}:* {len(c)} cuentas" for s, c in stock.items()]
        await query.message.reply_text("\n".join(lineas) or "📭 Sin stock")
    elif data == "cmds":
        await query.message.reply_text(
            "📖 Comandos:\n"
            "• /key <clave>\n"
            "• /get <sitio> <cant>\n"
            "• /gen /upload /edit /del /users"
        )

# ---------- main ----------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", key_cmd))
    app.add_handler(CommandHandler("get", get_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("gen", gen_cmd))
    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("edit", edit_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_del))
    app.add_handler(CallbackQueryHandler(callback))
    print("✅ AlphaChecker v6.1 listo.")
    app.run_polling()

if __name__ == "__main__":
    main()