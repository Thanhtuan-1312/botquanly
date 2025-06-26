from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# --- KẾT NỐI GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ['GOOGLE_CREDENTIALS']), scope)
client = gspread.authorize(creds)
sheet = client.open("Bảng tính không có tiêu đề").sheet1

# --- TRẠNG THÁI ---
IMEI, TEN, PHI, NGAY = range(4)
SUA_IMEI, SUA_TEN, SUA_PHI, SUA_NGAY = range(4, 8)

# --- /new ---
async def start_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👉 Nhập IMEI thiết bị:")
    return IMEI

async def nhap_imei(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["imei"] = update.message.text
    await update.message.reply_text("👉 Nhập tên khách hàng:")
    return TEN

async def nhap_ten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ten"] = update.message.text
    await update.message.reply_text("👉 Nhập phí dịch vụ:")
    return PHI

async def nhap_phi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phi"] = update.message.text
    await update.message.reply_text("👉 Nhập ngày lên đơn (vd: 26/06):")
    return NGAY

async def nhap_ngay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ngay"] = update.message.text
    sheet.append_row([
        context.user_data["imei"],
        context.user_data["ten"],
        context.user_data["phi"],
        context.user_data["ngay"],
        "Chưa làm"
    ])
    await update.message.reply_text("✅ Đã thêm đơn hàng thành công!")
    return ConversationHandler.END

async def huy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Đã huỷ thao tác.")
    return ConversationHandler.END

# --- /xong ---
async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        row_num = int(context.args[0])
        sheet.update_cell(row_num + 1, 5, "Đã làm")
        await update.message.reply_text(f"✅ Đã đánh dấu đơn hàng số {row_num} là ĐÃ LÀM.")
    except:
        await update.message.reply_text("❌ Dùng đúng: /xong 1")

# --- /xoa ---
async def xoa_don(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(context.args[0])
        sheet.delete_rows(index + 1)
        await update.message.reply_text(f"🗑️ Đã xoá đơn hàng số {index}.")
    except:
        await update.message.reply_text("❌ Dùng đúng: /xoa 1")

# --- /sua ---
async def sua_don(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(context.args[0])
        context.user_data["sua_index"] = index + 1
        await update.message.reply_text("👉 Nhập IMEI mới:")
        return SUA_IMEI
    except:
        await update.message.reply_text("❌ Dùng đúng: /sua 1")
        return ConversationHandler.END

async def sua_imei(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["imei"] = update.message.text
    await update.message.reply_text("👉 Nhập tên khách mới:")
    return SUA_TEN

async def sua_ten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ten"] = update.message.text
    await update.message.reply_text("👉 Nhập phí mới:")
    return SUA_PHI

async def sua_phi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phi"] = update.message.text
    await update.message.reply_text("👉 Nhập ngày mới:")
    return SUA_NGAY

async def sua_ngay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = context.user_data["sua_index"]
    sheet.update(f"A{row}:D{row}", [[
        context.user_data["imei"],
        context.user_data["ten"],
        context.user_data["phi"],
        update.message.text
    ]])
    await update.message.reply_text("✅ Đã sửa đơn hàng.")
    return ConversationHandler.END

# --- /danhsach ---
async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheet.get_all_values()[1:]
    chua, da = "", ""
    for i, row in enumerate(rows, start=1):
        dong = f"{i}. IMEI: {row[0]}, Tên: {row[1]}, Phí: {row[2]}, Ngày: {row[3]}\n"
        if row[4] == "Chưa làm":
            chua += dong
        else:
            da += dong
    reply = f"🟡 CHƯA LÀM:\n{chua or 'Không có'}\n\n✅ ĐÃ LÀM:\n{da or 'Không có'}"
    await update.message.reply_text(reply)

# --- CHẠY BOT ---
app = Application.builder().token("8087512449:AAESO0h28OQYaxwHL8JR4gf16vYDwE3QGaQ").build()

# Handler cho /new
new_handler = ConversationHandler(
    entry_points=[CommandHandler("new", start_new)],
    states={
        IMEI: [MessageHandler(filters.TEXT & ~filters.COMMAND, nhap_imei)],
        TEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, nhap_ten)],
        PHI: [MessageHandler(filters.TEXT & ~filters.COMMAND, nhap_phi)],
        NGAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, nhap_ngay)],
    },
    fallbacks=[CommandHandler("cancel", huy)]
)

# Handler cho /sua
sua_handler = ConversationHandler(
    entry_points=[CommandHandler("sua", sua_don)],
    states={
        SUA_IMEI: [MessageHandler(filters.TEXT & ~filters.COMMAND, sua_imei)],
        SUA_TEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, sua_ten)],
        SUA_PHI: [MessageHandler(filters.TEXT & ~filters.COMMAND, sua_phi)],
        SUA_NGAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sua_ngay)],
    },
    fallbacks=[CommandHandler("cancel", huy)]
)

# Thêm handler vào bot
app.add_handler(new_handler)
app.add_handler(sua_handler)
app.add_handler(CommandHandler("xoa", xoa_don))
app.add_handler(CommandHandler("xong", mark_done))
app.add_handler(CommandHandler("danhsach", list_orders))

print("🤖 Bot đang chạy...")
app.run_polling()
