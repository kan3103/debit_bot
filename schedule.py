from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import calendar
import json
import os

DATA_FILE = f"D:/Debit/{datetime.now().year}"
schedules = []
class Schedule():
    def __init__(self, money, content):
        self.money = money
        self.content = content

def load_data():
    global schedules
    try:
        month = datetime.now().month
        date = datetime.now().day
        with open(f"{DATA_FILE}/Tháng {month}/Ngày {date}", "r",encoding='utf-8') as file:
            data = json.load(file)
            if data.get("chitieu") is None:
                schedules = []
            else:
                schedules = [
                    Schedule( item["money"], item["content"])
                    for item in data.get("chitieu", [])
                ]
    except FileNotFoundError:
        schedules = []

def save_data():
    global schedules
    data = {
        "chitieu": [
            {
                "money": schedule.money,
                "content": schedule.content
            }
            for schedule in schedules
        ],
    }
    month = datetime.now().month
    date = datetime.now().day
    if not os.path.exists(f"{DATA_FILE}/Tháng {month}"):
        os.makedirs(f"{DATA_FILE}/Tháng {month}")
        

    with open(f"{DATA_FILE}/Tháng {month}/Ngày {date}", "w", encoding='utf-8' ) as file:
        json.dump(data, file, ensure_ascii=False)
    
        
async def note(update: Update, context: ContextTypes):
    global schedules
    if len(context.args) < 2:
        await update.message.reply_text("Sai cú pháp: /savemoney [số tiền] [nội dung]")
        return
    money = context.args[0]
    content = context.args[1:]
    content = str(" ".join(content))
    schedule = Schedule(money, content)
    schedules.append(schedule)
    save_data()
    await update.message.reply_text(f"Bạn đã xài {money} cho {content}")
    
async def check(update: Update, context: ContextTypes):
    global schedules
    
    if len(context.args) < 1:
        sum = 0
        for schedule in schedules:
            await update.message.reply_text(f"{schedule.money} {schedule.content}")
            sum += int(schedule.money[:-1]) * 1000 if schedule.money[-1] == "k" else int(schedule.money)
        await update.message.reply_text(f"Tổng số tiền đã xài hôm nay: {sum}")
        return
    elif len(context.args) == 3:
        try:
            sum = 0
            day = int(context.args[1])
            month = int(context.args[2])
            year = datetime.now().year
            if day < 1 or day > calendar.monthrange(year, month)[1] or month < 1 or month > 12:
                await update.message.reply_text("Ngày tháng không hợp lệ")
                return
            try:
                with open(f"{DATA_FILE}/Tháng {month}/Ngày {str(day)}", "r",encoding='utf-8') as file:
                    data = json.load(file)
                    if data.get("chitieu") is None:
                        temp = []
                    else:
                        temp = [
                            Schedule( item["money"], item["content"])
                            for item in data.get("chitieu", [])
                        ]
                for schedule in temp:
                    await update.message.reply_text(f"{schedule.money} {schedule.content}")
                    sum += int(schedule.money[:-1]) * 1000 if schedule.money[-1] == "k" else int(schedule.money)
                await update.message.reply_text(f"Tổng số tiền đã xài ngày {day} tháng {month}: {sum}")
            except FileNotFoundError:
                await update.message.reply_text("Không có dữ liệu ngày này")
                return
        except ValueError:
            await update.message.reply_text("Sai cú pháp: /check ngày [ngày] [tháng]")
            return
    else:
        await update.message.reply_text("Sai cú pháp: /check ngày [ngày] [tháng]")
        return
async def month(update: Update, context: ContextTypes):
    global schedules
    if len(context.args) < 1:
        month = datetime.now().month
        year = datetime.now().year
        sum = 0
        try:
            for i in range(1, calendar.monthrange(year, month)[1] + 1):
                try:
                    temp_sum = 0
                    with open(f"{DATA_FILE}/Tháng {month}/Ngày {str(i)}", "r",encoding='utf-8') as file:
                        data = json.load(file)
                        if data.get("chitieu") is None:
                            temp = []
                        else:
                            temp = [
                                Schedule( item["money"], item["content"])
                                for item in data.get("chitieu", [])
                            ]
                    for schedule in temp:
                        #await update.message.reply_text(f"{schedule.money} {schedule.content}")
                        temp_sum += int(schedule.money[:-1]) * 1000 if schedule.money[-1] == "k" else int(schedule.money)
                    await update.message.reply_text(f"Ngày {i}: {temp_sum}")
                    sum += temp_sum
                except FileNotFoundError:
                    #await update.message.reply_text(f"Không có dữ liệu ngày {i}")
                    continue
            await update.message.reply_text(f"Tổng số tiền đã xài tháng {month}: {sum}")
        except FileNotFoundError:
                await update.message.reply_text("Không có dữ liệu tháng này")
                return
    elif len(context.args) == 1:
        try:
            sum = 0
            month = int(context.args[0])
            year = datetime.now().year
            if month < 1 or month > 12:
                await update.message.reply_text("Tháng không hợp lệ")
                return
            try:
                for i in range(1, calendar.monthrange(year, month)[1] + 1):
                    try:
                        temp_sum = 0
                        with open(f"{DATA_FILE}/Tháng {month}/Ngày {str(i)}", "r",encoding='utf-8') as file:
                            data = json.load(file)
                            if data.get("chitieu") is None:
                                temp = []
                            else:
                                temp = [
                                    Schedule( item["money"], item["content"])
                                    for item in data.get("chitieu", [])
                                ]
                        for schedule in temp:
                            #await update.message.reply_text(f"{schedule.money} {schedule.content}")
                            temp_sum += int(schedule.money[:-1]) * 1000 if schedule.money[-1] == "k" else int(schedule.money)
                        await update.message.reply_text(f"Ngày {i}: {temp_sum}")
                        sum += temp_sum
                    except FileNotFoundError:
                        #await update.message.reply_text(f"Không có dữ liệu ngày {i}")
                        continue
                await update.message.reply_text(f"Tổng số tiền đã xài tháng {month}: {sum}")
            except FileNotFoundError:
                await update.message.reply_text("Không có dữ liệu tháng này")
                return
        except ValueError:
            await update.message.reply_text("Sai cú pháp: /month [tháng]")
            return
    else:
        await update.message.reply_text("Sai cú pháp: /month [tháng]")
        return

def main():
    #load excel file to table and  debits
    # Thay YOUR_API_TOKEN bằng API Token của bạn
    TOKEN = "7892436573:AAG9H4pQqXw6Sbg1GmZCMXabvZml7CYv_ZM"
    if not os.path.exists(f"{DATA_FILE}"):
        os.makedirs(f"{DATA_FILE}")
    global schedules
    load_data()
    
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("note", note))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("month", month))

    application.run_polling()

if __name__ == "__main__":
    main()
