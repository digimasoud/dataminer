import pandas as pd
import requests
import os
import time
import json

# فایل CSV و ستون‌ها
csv_file = 'out.csv'  # مسیر فایل CSV
url_column = 'imageUrl'  # ستون لینک‌ها
name_column = 'instagramID'  # ستون نام فایل‌ها
output_folder = 'images1/'  # پوشه ذخیره‌سازی تصاویر
config_file = 'imageconfig.json'  # فایل کانفیگ برای ذخیره‌سازی وضعیت دانلود

# ایجاد پوشه برای ذخیره تصاویر
os.makedirs(output_folder, exist_ok=True)

# خواندن لینک‌ها و نام‌ها از CSV
df = pd.read_csv(csv_file)

# حذف ردیف‌هایی که لینک یا نام خالی دارند
df = df.dropna(subset=[url_column, name_column])

# تبدیل ستون نام به رشته و حذف `.0` اگر وجود داشته باشد
df[name_column] = df[name_column].astype(str).str.replace(r'\.0$', '', regex=True)

# خواندن وضعیت دانلود قبلی از فایل کانفیگ اگر وجود داشته باشد
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    last_downloaded_index = config_data.get('last_downloaded_index', -1)  # مقدار پیش‌فرض -1 برای شروع از ابتدا
else:
    last_downloaded_index = -1

# دانلود تصاویر
for index, row in df.iterrows():
    if index <= last_downloaded_index:
        # اگر این تصویر قبلاً دانلود شده است، ادامه بده
        continue
    
    url = row[url_column]
    file_name = row[name_column]
    
    # مسیر کامل فایل
    file_path = os.path.join(output_folder, f"{file_name}.jpg")

    if os.path.exists(file_path):
        # اگر تصویر قبلاً دانلود شده، آن را رد کن
        print(f"Skipped (already downloaded): {file_name}")
        continue

    try:
        # دانلود تصویر با timeout و جلوگیری از توقف در صورت خطا
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {file_name}")
        else:
            print(f"Failed to download (HTTP {response.status_code}): {url}")
        
        # ذخیره وضعیت دانلود در فایل کانفیگ
        with open(config_file, 'w') as f:
            json.dump({'last_downloaded_index': index}, f)

        # تأخیر 2 ثانیه‌ای بین درخواست‌ها
        time.sleep(2)
    except requests.exceptions.RequestException as e:
        # ثبت خطا و ادامه پردازش
        print(f"Error downloading {url}: {e}")
        continue
