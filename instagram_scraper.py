import instaloader
import time
import requests
import csv
import os
import json
import logging
import sys
from threading import Timer

# تنظیم لاگ‌گیری
logging.basicConfig(
    filename="script.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# انتقال پیام‌های خطای Instaloader به فایل لاگ
sys.stderr = open("error.log", "a")

def timeout_handler(session, tag, session_id, config_file):
    """غیرفعال کردن سشن در صورت عدم دریافت داده در زمان مشخص"""
    logging.error(f"سشن {tag} به دلیل تایم‌اوت غیرفعال شد.")
    for session_data in config_file["sessions"]:
        if session_data["session_id"] == session_id:
            session_data["session_id"] = f"#{session_id}"
            session_data["tag"] += " - Disabled"
    update_config("config.json", config_file)

def get_instagram_data(username, session, category, city, config_file, tag, session_id):
    """دریافت داده‌های اینستاگرام برای یک لینک پروفایل با تایم‌اوت"""
    L = instaloader.Instaloader()
    timer = Timer(10.0, timeout_handler, [session, tag, session_id, config_file])  # تایم‌اوت 10 ثانیه
    try:
        timer.start()
        L.context._session = session
        profile = instaloader.Profile.from_username(L.context, username)
        timer.cancel()

        # اطلاعات عمومی پروفایل
        business_phone_number = profile.business_phone_number if hasattr(profile, 'business_phone_number') else "ندارد"
        business_email = profile.business_email if hasattr(profile, 'business_email') else "ندارد"
        business_address = profile.business_address if hasattr(profile, 'business_address') else "ندارد"
        website_link = profile.external_url if hasattr(profile, 'external_url') else "ندارد"

        data = {
            "instagramID": profile.userid,
            "Username": profile.username,
            "query": f"https://www.instagram.com/{profile.username}/",
            "Full Name": profile.full_name,
            "followersCount": profile.followers,
            "followingCount": profile.followees,
            "PostCount": profile.mediacount,
            "bio": profile.biography,
            "website": website_link,
            "Is Private": profile.is_private,
            "Is Verified": profile.is_verified,
            "imageUrl": profile.profile_pic_url,
            "Category": category,
            "City": city,
            "Business Phone Number": business_phone_number,
            "Business Email": business_email,
            "Business Address": business_address,
            "Website Link": website_link
        }

        logging.info(f"داده‌های پروفایل {username} با موفقیت دریافت شد.")
        return data
    except instaloader.exceptions.ProfileNotExistsException:
        timer.cancel()
        logging.warning(f"پروفایل {username} یافت نشد.")
        return None
    except Exception as e:
        timer.cancel()
        logging.error(f"خطا در دریافت اطلاعات برای {username}: {str(e)}")
        return None
    finally:
        if timer.is_alive():
            timer.cancel()

def create_sessions(session_data, max_active_sessions=5):
    """ایجاد سشن‌های اینستاگرام با استفاده از session_id های مختلف و محدود کردن تعداد سشن‌های فعال"""
    sessions = []
    active_count = 0
    for session in session_data:
        if active_count >= max_active_sessions:
            logging.warning("تعداد سشن‌های فعال به حداکثر رسیده است.")
            break
        session_id = session["session_id"]
        if session_id.startswith("#"):
            logging.info(f"سشن غیرفعال: {session['tag']}")
            continue
        session_obj = requests.Session()
        session_obj.cookies.set("sessionid", session_id, domain=".instagram.com")
        sessions.append((session_obj, session["tag"], session_id))
        active_count += 1
    logging.info(f"تعداد سشن‌های فعال: {active_count}")
    return sessions

def update_input_file(input_file, failed_indices):
    """به‌روزرسانی فایل ورودی و اضافه کردن ستاره به ستون D برای لینک‌های ناموفق"""
    with open(input_file, 'r', encoding='utf-8') as file:
        rows = list(csv.reader(file))

    for index in failed_indices:
        if len(rows[index]) <= 3:
            rows[index].extend(["*"])
        else:
            rows[index][3] = "*"

    with open(input_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    logging.info(f"فایل ورودی به‌روزرسانی شد. تعداد لینک‌های ناموفق: {len(failed_indices)}")

def validate_input_file(input_file):
    """بررسی فایل ورودی و حذف یا نادیده گرفتن سطرهای ناقص"""
    valid_rows = []
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader, None)  # رد کردن سطر هدر
        if header:
            valid_rows.append(header)
        for row in reader:
            if len(row) < 3 or not row[0]:
                logging.warning(f"سطر ناقص یافت شد و نادیده گرفته شد: {row}")
                continue
            valid_rows.append(row)

    with open(input_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(valid_rows)
    logging.info(f"فایل ورودی اعتبارسنجی و به‌روزرسانی شد.")

def update_config(config_file, config_data):
    """به‌روزرسانی فایل کانفیگ با وضعیت جدید"""
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(config_data, file, ensure_ascii=False, indent=4)
    logging.info("فایل کانفیگ به‌روزرسانی شد.")

def process_usernames(links, sessions, output_file, start_index, count, categories_and_cities, delay, config_file):
    if not sessions:
        logging.error("هیچ سشن معتبری برای پردازش موجود نیست.")
        return start_index  # بازگشت به ایندکس شروع در صورت نبود سشن معتبر

    results = []
    failed_indices = []
    session_count = len(sessions)
    end_index = min(start_index + count, len(links))

    for i, link in enumerate(links[start_index:end_index], start=start_index):
        session, tag, session_id = sessions[i % session_count]  # انتخاب سشن برای این لینک
        logging.info(f"در حال پردازش {link} ({i + 1}/{end_index}) با سشن {i % session_count + 1} ({tag})...")

        username = link.split('/')[-2]  # استخراج نام کاربری از لینک پروفایل
        category, city = categories_and_cities[i]

        try:
            data = get_instagram_data(username, session, category, city, config_file, tag, session_id)
            if data:
                results.append(data)
            else:
                logging.warning(f"داده‌ای برای {username} یافت نشد.")
        except Exception as e:
            logging.error(f"خطای سشن {i % session_count + 1} ({tag}): {str(e)}")
            failed_indices.append(i)
            continue

        time.sleep(delay)  # تاخیر بین درخواست‌ها

        # ذخیره نتایج در فایل CSV بعد از هر پروفایل
        if results:
            keys = results[0].keys()
            with open(output_file, 'a', newline='', encoding='utf-8') as output:
                writer = csv.DictWriter(output, fieldnames=keys)
                if i == start_index:  # فقط در اولین نوشتن هدر را اضافه کن
                    writer.writeheader()
                writer.writerow(results[-1])

        # به‌روزرسانی فایل کانفیگ پس از هر پردازش موفق
        config_file["last_processed_index"] = i + 1
        update_config("config.json", config_file)

    logging.info(f"نتایج در فایل {output_file} ذخیره شد.")
    return end_index  # برگرداندن ایندکس آخرین پروفایل پردازش شده

def main():
    config_file = "config.json"  # فایل کانفیگ

    # بارگذاری تنظیمات سشن‌ها
    with open(config_file, 'r', encoding='utf-8') as file:
        config = json.load(file)

    session_data = config["sessions"]
    max_active_sessions = config.get("max_active_sessions", 5)
    sessions = create_sessions(session_data, max_active_sessions)

    # دریافت تنظیمات اولیه
    input_file = config["input_file"]
    output_file = config["output_file"]
    delay = config["delay"]
    count = config["count"]

    # بررسی فایل ورودی
    validate_input_file(input_file)

    # خواندن لینک‌ها، دسته‌بندی و شهر از فایل CSV
    links = []
    categories_and_cities = []  # اینجا دسته‌بندی و شهرها ذخیره می‌شوند
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # رد کردن سطر هدر
        for row in reader:
            links.append(row[0])  # لینک پروفایل در ستون اول
            category = row[1] if len(row) > 1 else ""
            city = row[2] if len(row) > 2 else ""
            categories_and_cities.append((category, city))

    # پردازش لینک‌ها
    start_index = config.get("last_processed_index", 0)
    last_processed = process_usernames(links, sessions, output_file, start_index, count, categories_and_cities, delay, config)

    # به‌روزرسانی کانفیگ با ایندکس جدید
    config["last_processed_index"] = last_processed
    update_config(config_file, config)

    logging.info(f"پردازش تا لینک شماره {last_processed} از {len(links)} انجام شد.")

if __name__ == "__main__":
    main()
