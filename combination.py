import csv

# فایل‌های ورودی و خروجی
categories_file = "categories.txt"
neighborhoods_file = "neighborhoods.csv"
output_file = "combinations.csv"

# تابع برای خواندن دسته‌بندی‌ها از فایل متنی
def read_categories(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines() if line.strip()]

# تابع برای خواندن محله‌ها از فایل CSV
def read_neighborhoods(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        return [(row[0], row[1] if len(row) > 1 and row[1].strip() else "") for row in reader if row]

# ایجاد ترکیب‌ها و ذخیره در فایل CSV
def create_combinations(categories, neighborhoods, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        # نوشتن سرستون‌ها
        writer.writerow(["دسته‌بندی", "محله", "ترکیب"])
        # ایجاد ترکیب‌ها
        for category in categories:
            for neighborhood, city in neighborhoods:
                location = f"{neighborhood},{city}".strip(", ")
                combination = f"{category} {neighborhood} {city}".strip()
                writer.writerow([category, location, combination])

# اجرای برنامه
if __name__ == "__main__":
    try:
        categories = read_categories(categories_file)
        neighborhoods = read_neighborhoods(neighborhoods_file)
        create_combinations(categories, neighborhoods, output_file)
        print(f"ترکیب‌ها با موفقیت در فایل '{output_file}' ذخیره شدند.")
    except Exception as e:
        print(f"خطایی رخ داد: {e}")
