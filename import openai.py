import requests
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os

# فایل‌های تنظیمات
SETTINGS_FILE = "settings.json"
API_KEY_FILE = "api_key.txt"

# آدرس‌های API AvalAI
BASE_URL_CREDIT = "https://api.avalai.ir/user/credit"
BASE_URL_CHAT = "https://api.avalai.ir/v1/chat/completions"

# مدیریت تنظیمات
def save_settings(settings):
    """ذخیره تنظیمات در فایل JSON"""
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file)

def load_settings():
    """بارگذاری تنظیمات از فایل JSON"""
    try:
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "input_file": "",
            "output_file": "",
            "input_column": "",
            "output_column": "",
            "prompt_template": "",
            "model": "gpt-3.5-turbo",
            "max_rows": 0,
            "last_processed_line": 0,
        }

# مدیریت کلید API
def save_api_key(api_key):
    """ذخیره API Key در فایل"""
    with open(API_KEY_FILE, "w") as file:
        file.write(api_key)

def load_api_key():
    """خواندن API Key از فایل"""
    try:
        with open(API_KEY_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

# بارگذاری API Key
API_KEY = load_api_key()

# دریافت موجودی
def get_user_credit():
    """دریافت موجودی از API"""
    if not API_KEY:
        return "API Key وارد نشده است."
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(BASE_URL_CREDIT, headers=headers)
        if response.status_code == 200:
            return response.json().get("credit", "نامشخص")
        else:
            return f"خطا: {response.status_code}"
    except Exception as e:
        return f"خطا در ارتباط با API: {e}"

# ارسال درخواست به API AvalAI
def generate_response(prompt, model="gpt-3.5-turbo"):
    """ارسال پرامپت به AvalAI و دریافت پاسخ"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    try:
        response = requests.post(BASE_URL_CHAT, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"خطا: {response.status_code}, {response.text}")
    except Exception as e:
        return f"خطا در ارتباط با AvalAI: {e}"

# پردازش فایل CSV
def process_csv(input_file, output_file, input_column, output_column, prompt_template, max_rows, model, start_line):
    try:
        df = pd.read_csv(input_file)

        if input_column not in df.columns:
            messagebox.showerror("Error", f"ستون '{input_column}' در فایل پیدا نشد.")
            return

        if os.path.exists(output_file):
            df_output = pd.read_csv(output_file)
        else:
            df_output = pd.DataFrame(columns=df.columns)

        if output_column not in df_output.columns:
            df_output[output_column] = ""

        total_rows = len(df)
        progress_bar["maximum"] = total_rows  # تنظیم نوار پیشرفت

        processed_count = 0  # شمارنده پردازش‌ها

        for index, row in df.iterrows():
            if index < start_line:
                continue
            if max_rows and processed_count >= max_rows:
                break  # توقف پردازش پس از رسیدن به حداکثر

            text = row[input_column]
            if pd.isna(text):
                continue

            prompt = prompt_template.format(text)
            response = generate_response(prompt, model)
            row[output_column] = response
            df_output = pd.concat([df_output, pd.DataFrame([row])], ignore_index=True)

            start_line = index + 1
            processed_count += 1  # افزایش شمارنده
            last_line_entry.delete(0, tk.END)
            last_line_entry.insert(0, start_line)

            # به‌روزرسانی Progress Bar
            progress_bar["value"] = processed_count
            root.update_idletasks()

        df_output.to_csv(output_file, index=False)
        settings["last_processed_line"] = start_line
        save_settings(settings)
        messagebox.showinfo("Success", f"فایل خروجی به‌روزرسانی شد: {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"خطا در پردازش: {e}")

# مدیریت فایل‌ها
def open_file_dialog(entry_field):
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    entry_field.delete(0, tk.END)
    entry_field.insert(0, file_path)

def save_file_dialog(entry_field):
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    entry_field.delete(0, tk.END)
    entry_field.insert(0, file_path)

# به‌روزرسانی موجودی
def update_credit():
    credit = get_user_credit()
    credit_label.config(text=f"موجودی: {credit}")

# اجرای پردازش
def run_processing():
    settings["input_file"] = input_file_entry.get()
    settings["output_file"] = output_file_entry.get()
    settings["input_column"] = input_column_entry.get()
    settings["output_column"] = output_column_entry.get()
    settings["prompt_template"] = prompt_template_entry.get()
    settings["model"] = model_var.get()
    settings["max_rows"] = int(max_rows_entry.get() or 0)
    settings["last_processed_line"] = int(last_line_entry.get() or 0)

    save_settings(settings)

    if not settings["input_file"] or not settings["output_file"] or not settings["input_column"] or not settings["output_column"] or not settings["prompt_template"]:
        messagebox.showerror("Error", "لطفاً همه فیلدها را پر کنید.")
        return

    process_csv(
        settings["input_file"],
        settings["output_file"],
        settings["input_column"],
        settings["output_column"],
        settings["prompt_template"],
        settings["max_rows"],
        settings["model"],
        settings["last_processed_line"],
    )

# رابط کاربری
root = tk.Tk()
root.title("مدیریت فایل CSV با AvalAI")
root.geometry("600x800")

frame = tk.Frame(root)
frame.pack(pady=10)

# بارگذاری تنظیمات
settings = load_settings()

# API Key
tk.Label(frame, text="API Key:").grid(row=0, column=0, sticky="w")
api_key_entry = tk.Entry(frame, width=30)
api_key_entry.grid(row=0, column=1)
api_key_entry.insert(0, API_KEY)
tk.Button(frame, text="ذخیره", command=lambda: save_api_key(api_key_entry.get())).grid(row=0, column=2)

# موجودی
credit_label = tk.Label(root, text="موجودی: ...")
credit_label.pack(pady=10)
tk.Button(root, text="به‌روزرسانی موجودی", command=update_credit).pack()

# فایل‌های ورودی و خروجی
tk.Label(frame, text="فایل ورودی CSV:").grid(row=1, column=0, sticky="w")
input_file_entry = tk.Entry(frame, width=30)
input_file_entry.grid(row=1, column=1)
input_file_entry.insert(0, settings["input_file"])
tk.Button(frame, text="انتخاب", command=lambda: open_file_dialog(input_file_entry)).grid(row=1, column=2)

tk.Label(frame, text="فایل خروجی CSV:").grid(row=2, column=0, sticky="w")
output_file_entry = tk.Entry(frame, width=30)
output_file_entry.grid(row=2, column=1)
output_file_entry.insert(0, settings["output_file"])
tk.Button(frame, text="ذخیره", command=lambda: save_file_dialog(output_file_entry)).grid(row=2, column=2)

# ستون‌های ورودی و خروجی
tk.Label(frame, text="ستون ورودی:").grid(row=3, column=0, sticky="w")
input_column_entry = tk.Entry(frame, width=30)
input_column_entry.grid(row=3, column=1)
input_column_entry.insert(0, settings["input_column"])

tk.Label(frame, text="ستون خروجی:").grid(row=4, column=0, sticky="w")
output_column_entry = tk.Entry(frame, width=30)
output_column_entry.grid(row=4, column=1)
output_column_entry.insert(0, settings["output_column"])

# قالب پرامپت و مدل
tk.Label(frame, text="قالب پرامپت:").grid(row=5, column=0, sticky="w")
prompt_template_entry = tk.Entry(frame, width=30)
prompt_template_entry.grid(row=5, column=1)
prompt_template_entry.insert(0, settings["prompt_template"])

tk.Label(frame, text="مدل انتخابی:").grid(row=6, column=0, sticky="w")
model_var = tk.StringVar(value=settings["model"])
model_menu = ttk.Combobox(frame, textvariable=model_var, values=["gpt-3.5-turbo", "gpt-4"])
model_menu.grid(row=6, column=1)

# تعداد پردازش
tk.Label(frame, text="تعداد پردازش (۰ برای همه):").grid(row=7, column=0, sticky="w")
max_rows_entry = tk.Entry(frame, width=30)
max_rows_entry.grid(row=7, column=1)
max_rows_entry.insert(0, str(settings["max_rows"]))

# آخرین خط پردازش‌شده
tk.Label(frame, text="آخرین خط پردازش‌شده:").grid(row=8, column=0, sticky="w")
last_line_entry = tk.Entry(frame, width=30)
last_line_entry.grid(row=8, column=1)
last_line_entry.insert(0, str(settings["last_processed_line"]))

# Progress Bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

# دکمه اجرا
tk.Button(root, text="شروع پردازش", command=run_processing, bg="green", fg="white").pack(pady=10)

root.mainloop()
