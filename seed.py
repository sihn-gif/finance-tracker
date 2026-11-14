"""Tạo dữ liệu mẫu: python seed.py"""
import random
from datetime import date, timedelta

from app import create_app, services
from app.models import Category, Transaction, db

random.seed(42)
app = create_app()

with app.app_context():
    Transaction.query.delete()
    db.session.commit()
    cats = {c.name: c.id for c in Category.query.all()}
    today = date.today()
    for months_ago in range(3):
        first = (today.replace(day=1) - timedelta(days=30 * months_ago)).replace(day=1)
        services.add_transaction(12_000_000, first.isoformat(), cats["Lương"], "Lương tháng")
        for _ in range(random.randint(25, 35)):
            name = random.choice(["Ăn uống"] * 5 + ["Đi lại"] * 3 + ["Giải trí", "Học tập", "Khác"])
            amount = random.randrange(20_000, 300_000, 5_000)
            day = first + timedelta(days=random.randint(0, 27))
            if day <= today:
                services.add_transaction(amount, day.isoformat(), cats[name], "Dữ liệu mẫu")
        services.add_transaction(3_000_000, first.isoformat(), cats["Nhà ở"], "Tiền phòng")
    print("Đã tạo dữ liệu mẫu.")
