"""Business logic. Routes call these functions; unit tests test them directly."""
from datetime import date, datetime

from sqlalchemy import func

from .models import Budget, Category, Transaction, db

DEFAULT_CATEGORIES = [
    ("Lương", "income"),
    ("Thu nhập khác", "income"),
    ("Ăn uống", "expense"),
    ("Đi lại", "expense"),
    ("Nhà ở", "expense"),
    ("Giải trí", "expense"),
    ("Học tập", "expense"),
    ("Khác", "expense"),
]

WARNING_PERCENT = 80
EXCEEDED_PERCENT = 100


def ensure_default_categories():
    if Category.query.count() == 0:
        for name, type_ in DEFAULT_CATEGORIES:
            db.session.add(Category(name=name, type=type_))
        db.session.commit()


# ---------- validation ----------
def parse_amount(value):
    try:
        amount = int(value)
    except (TypeError, ValueError):
        raise ValueError("Số tiền phải là số nguyên.")
    if amount <= 0:
        raise ValueError("Số tiền phải lớn hơn 0.")
    return amount


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Ngày không hợp lệ (định dạng YYYY-MM-DD).")


def month_bounds(month):
    """'2026-11' -> (date(2026,11,1), date(2026,12,1))"""
    try:
        first = datetime.strptime(month, "%Y-%m").date()
    except (TypeError, ValueError):
        raise ValueError("Tháng không hợp lệ (định dạng YYYY-MM).")
    nxt = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    return first, nxt


# ---------- transactions ----------
def add_transaction(amount, date_str, category_id, note=""):
    amount = parse_amount(amount)
    day = parse_date(date_str)
    category = db.session.get(Category, category_id)
    if category is None:
        raise ValueError("Danh mục không tồn tại.")
    t = Transaction(amount=amount, date=day, category_id=category.id, note=(note or "")[:200])
    db.session.add(t)
    db.session.commit()
    return t


def delete_transaction(transaction_id):
    t = db.session.get(Transaction, transaction_id)
    if t is None:
        raise ValueError("Giao dịch không tồn tại.")
    db.session.delete(t)
    db.session.commit()


def list_transactions(month):
    first, nxt = month_bounds(month)
    return (
        Transaction.query.filter(Transaction.date >= first, Transaction.date < nxt)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .all()
    )


# ---------- reports ----------
def _totals_by_category(month, type_):
    first, nxt = month_bounds(month)
    rows = (
        db.session.query(Category.id, Category.name, func.sum(Transaction.amount))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(Category.type == type_, Transaction.date >= first, Transaction.date < nxt)
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    return [(cid, name, int(total)) for cid, name, total in rows]


def month_summary(month):
    income = sum(total for _, _, total in _totals_by_category(month, "income"))
    expense = sum(total for _, _, total in _totals_by_category(month, "expense"))
    return {"income": income, "expense": expense, "balance": income - expense}


def spending_by_category(month):
    return [(name, total) for _, name, total in _totals_by_category(month, "expense")]


# ---------- budgets ----------
def budget_level(spent, limit):
    percent = spent * 100 / limit
    if percent >= EXCEEDED_PERCENT:
        return "exceeded"
    if percent >= WARNING_PERCENT:
        return "warning"
    return "ok"


def set_budget(category_id, month, limit):
    month_bounds(month)  # validates format
    limit = parse_amount(limit)
    category = db.session.get(Category, category_id)
    if category is None or category.type != "expense":
        raise ValueError("Chỉ đặt ngân sách cho danh mục chi tiêu.")
    if Budget.query.filter_by(category_id=category_id, month=month).first():
        raise ValueError("Danh mục này đã có ngân sách trong tháng.")
    b = Budget(category_id=category_id, month=month, limit_amount=limit)
    db.session.add(b)
    db.session.commit()
    return b


def budget_status(month):
    spent_by_id = {cid: total for cid, _, total in _totals_by_category(month, "expense")}
    result = []
    for b in Budget.query.filter_by(month=month).all():
        spent = spent_by_id.get(b.category_id, 0)
        result.append({
            "category": b.category.name,
            "limit": b.limit_amount,
            "spent": spent,
            "percent": round(spent * 100 / b.limit_amount),
            "level": budget_level(spent, b.limit_amount),
        })
    return result
