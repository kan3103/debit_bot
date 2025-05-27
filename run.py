from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Danh sách lưu thông tin người dùng đã tham gia bàn
table = []
debits = []


import json

# File lưu trữ dữ liệu
DATA_FILE = "D:/Debit/game_data.json"

# Hàm lưu dữ liệu
def save_data():
    global table, debits
    data = {
        "table": table,
        "debits": [
            {
                "user_id1": debit.user_id1,
                "user_id2": debit.user_id2,
                "amount": debit.amount,
            }
            for debit in debits
        ],
    }
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

# Hàm tải dữ liệu
def load_data():
    global table, debits
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            table = data.get("table", [])
            debits = [
                Debit(item["user_id1"], item["user_id2"], item["amount"])
                for item in data.get("debits", [])
            ]
    except FileNotFoundError:
        # Nếu file không tồn tại, bắt đầu với dữ liệu trống
        table = []
        debits = []

class Debit():
    def __init__(self, user_id1, user_id2, amount):
        self.user_id1 = user_id1
        self.user_id2 = user_id2
        self.amount = amount

    def checkamount(self,user_id):
        if user_id == self.user_id1:
            for player in table:
                if player["id"] == self.user_id2:
                    return "Bạn nợ "+ player["first_name"]+" "  + str(abs(self.amount)) if self.amount < 0 else "Bạn cho "+ player["first_name"] +" " +str(abs(self.amount))
        if user_id == self.user_id2:
             for player in table:
                if player["id"] == self.user_id1:
                    return "Bạn nợ "+ player["first_name"] +" " + str(abs(self.amount)) if self.amount > 0 else "Bạn cho "+ player["first_name"] +" "+ str(abs(self.amount))

        return "sai id"

    def note(self,user_id,money):
        if user_id == self.user_id1:
            self.amount += money
        if user_id == self.user_id2:
            self.amount -= money
        save_data() 

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global table
    user = update.effective_user
    user_data = {
        "id": user.id,
        "username": user.username or "No username",
        "first_name": user.first_name or "No first name",
    }

    if any(player["id"] == user.id for player in table):
        await update.message.reply_text("Bạn đã tham gia bàn chơi rồi!")
        return

    table.append(user_data)
    save_data() 
    await update.message.reply_text(f"{user.first_name} đã tham gia bàn chơi!")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global table
    user = update.effective_user

    if not table:
        await update.message.reply_text("Hiện tại chưa có ai tham gia bàn chơi. Dùng lệnh /join để tham gia.")
        return

    if not any(player["id"] == user.id for player in table):
        await update.message.reply_text("Bạn chưa tham gia bàn chơi. Dùng lệnh /join để tham gia.")
        return

    message = f"{user.first_name} vừa mua đồ!"
    for player in table:
        await context.bot.send_message(chat_id=player["id"], text=message)

async def list_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global table

    if not table:
        await update.message.reply_text("Hiện tại chưa có ai trong bàn chơi.")
        return

    player_list = "\n".join([f"- {player['first_name']} (@{player['username']}) ID: {player['id']}" for player in table])
    await update.message.reply_text(f"Danh sách người chơi trong bàn:\n{player_list}")

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global debit
    user = update.effective_user
    # Kiểm tra có tham số
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Bạn cần nhập theo cú pháp: /note [Tên người] [Số tiền].")
        return
    
    # Lấy các tham số từ context.args
    name = context.args[0]  # Tên người
    try:
        amount = context.args[1]  # Số tiền
        if amount[-1].lower() == 'k':  # Kiểm tra nếu số tiền có ký hiệu 'k'
            amount = int(amount[:-1]) * 1000
        else:
            amount = int(amount)
    except ValueError:
        await update.message.reply_text("Số tiền không hợp lệ. Vui lòng nhập lại.")
        return
    if not any(player["id"] == user.id for player in table):
        await update.message.reply_text("Bạn chưa tham gia bàn chơi!")
        return
    else:
        for player in table:
            if player["first_name"] == name:
                if player["id"] == user.id:
                    await update.message.reply_text("Bạn không thể nợ chính mình.")
                    return
                else:
                    for debit in debits:
                        if debit.user_id1 == user.id and debit.user_id2 == player["id"]:
                            debit.note(user.id, amount)
                            await update.message.reply_text(f"{user.first_name} Đã thêm {name} với số tiền {amount:,} vào danh sách nợ.")
                            await context.bot.send_message(chat_id=player["id"], text=f"{user.first_name} Đã thêm {name} với số tiền {amount:,} vào danh sách nợ.")
                            return
                        if debit.user_id1 == player["id"] and debit.user_id2 == user.id:
                            debit.note(user.id, amount)
                            await update.message.reply_text(f"{user.first_name} Đã thêm {name} với số tiền {amount:,} vào danh sách nợ.")
                            await context.bot.send_message(chat_id=player["id"], text=f"{user.first_name} Đã thêm {name} với số tiền {amount:,} vào danh sách nợ.")
                            return
                    debits.append(Debit(user.id, player["id"], amount)) 
                    save_data() 
                    await update.message.reply_text(f"Đã thêm {name} với số tiền {amount:,} vào danh sách nợ.")
                    return
    
    

async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global debits
    user = update.effective_user
    print(debits)
    print(user.id)
    if not debits:
        print("Không có ai nợ bạn cả.")
        await update.message.reply_text("Không có ai nợ bạn cả.")
        return
    else:
        message = "Danh sách nợ của bạn:\n"
        for debit in debits:
            if debit.user_id1 == user.id or debit.user_id2 == user.id:
                message += debit.checkamount(user.id) + "\n"
        await update.message.reply_text(message)
    
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global table
    user = update.effective_user

    table = [player for player in table if player["id"] != user.id]
    save_data() 
    await update.message.reply_text(f"{user.first_name} đã rời khỏi bàn chơi.")

def main():
    #load excel file to table and  debits
    # Thay YOUR_API_TOKEN bằng API Token của bạn
    TOKEN = "7775578054:AAE9UoX17_Vgtinm96XFva7G6c_zsbAa9MA"
    global table, debits
    load_data()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("list", list_players))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CommandHandler("note", note))
    application.add_handler(CommandHandler("show", show))

    application.run_polling()

if __name__ == "__main__":
    main()
