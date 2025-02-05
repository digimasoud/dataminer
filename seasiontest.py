import json
import logging

import instaloader
from instaloader import Profile, ConnectionException, LoginRequiredException, QueryReturnedNotFoundException

logging.basicConfig(
    filename="session_validation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TARGET_USERNAME = "instagram"  # پیجی که می‌خواهیم تعداد فالورش را بررسی کنیم


def validate_sessions_instaloader_check_followers(config_file):
    """
    بررسی سشن‌های اینستاگرام با استفاده از Instaloader.
    برای تشخیص معتبر بودن سشن، تلاش می‌کنیم پروفایل 'instagram' را بخوانیم و تعداد فالورها را بگیریم.
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"خطا در خواندن فایل تنظیمات {config_file}: {e}")
        return

    sessions = config.get("sessions", [])
    if not sessions:
        logging.error("هیچ سشنی برای بررسی وجود ندارد.")
        return

    for session_info in sessions:
        session_id = session_info["session_id"]
        tag = session_info["tag"]

        was_disabled = session_id.startswith("#")
        real_session_id = session_id.lstrip("#")  # حذف '#' در ابتدای session_id

        logging.info(f"در حال بررسی سشن: {tag} (was_disabled={was_disabled})")

        # تست معتبر بودن سشن
        is_valid = test_session_by_followers(real_session_id)

        if is_valid:
            # اگر سشن معتبر است
            logging.info(f"✅ سشن معتبر: {tag}")
            if was_disabled:
                # قبلاً غیرفعال بوده، حالا معتبر شده → فعالش کنیم
                session_info["session_id"] = real_session_id
                session_info["tag"] = tag.replace(" - Disabled", "")
                logging.info(f"✅ سشن '{tag}' مجدداً فعال شد.")
        else:
            # اگر سشن نامعتبر است
            logging.warning(f"⚠️ سشن نامعتبر: {tag}")
            if not was_disabled:
                # اگر قبلاً فعال بود، حالا غیرفعالش کنیم
                session_info["session_id"] = "#" + session_info["session_id"]
                session_info["tag"] = f"{tag} - Disabled"
                logging.warning(f"⚠️ سشن '{tag}' غیرفعال شد.")

    # در پایان، تغییرات را در فایل کانفیگ ذخیره می‌کنیم
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.info("✅ وضعیت سشن‌ها ذخیره شد.")
    except Exception as e:
        logging.error(f"خطا در ذخیرهٔ فایل تنظیمات {config_file}: {e}")


def test_session_by_followers(session_id):
    """
    تلاش می‌کند با session_id به پیج TARGET_USERNAME دسترسی پیدا کند و تعداد فالورهایش را بخواند.
    اگر موفق شد، یعنی سشن معتبر است؛ در غیر این صورت، نامعتبر.
    """
    try:
        L = instaloader.Instaloader()

        # کوکی sessionid را داخل سشن Instaloader می‌گذاریم.
        # دقت کنید domain باید '.instagram.com' باشد.
        L.context._session.cookies.set("sessionid", session_id, domain=".instagram.com", path="/")

        # حالا می‌خواهیم اطلاعات پروفایل TARGET_USERNAME را بگیریم
        profile = Profile.from_username(L.context, TARGET_USERNAME)
        followers_count = profile.followers  # تعداد فالوورهای پیج

        logging.info(f"تعداد فالوورهای پیج @{TARGET_USERNAME} = {followers_count}")
        # اگر این دستور بدون خطا جواب داد، یعنی سشن معتبر بوده.
        return True

    except LoginRequiredException:
        # یعنی لازم است لاگین شویم اما sessionid معتبر نیست یا لاگین نشده‌ایم
        logging.warning("⚠️  سشن لاگین نیست (LoginRequiredException).")
        return False
    except QueryReturnedNotFoundException:
        # اگر پیج وجود نداشته باشد یا دسترسی نداشته باشیم
        logging.warning(f"⚠️  پیج @{TARGET_USERNAME} پیدا نشد یا دسترسی محدود.")
        return False
    except ConnectionException as ce:
        logging.error(f"🚨 خطای ConnectionException: {ce}")
        return False
    except Exception as e:
        logging.error(f"🚨 خطای غیرمنتظره در تست سشن با Instaloader: {e}")
        return False


if __name__ == "__main__":
    validate_sessions_instaloader_check_followers("config.json")
