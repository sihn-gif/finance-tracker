from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import services
from .models import Category

bp = Blueprint("main", __name__)


@bp.app_template_filter("vnd")
def vnd(n):
    return f"{n:,}".replace(",", ".") + " ₫"


def _current_month():
    month = request.values.get("month") or date.today().strftime("%Y-%m")
    try:
        services.month_bounds(month)
    except ValueError as e:
        flash(str(e), "error")
        month = date.today().strftime("%Y-%m")
    return month


def _shift_month(month, delta):
    """Dịch chuỗi 'YYYY-MM' tiến/lùi theo số tháng delta (VD: '2026-01', -1 -> '2025-12')."""
    year, m = map(int, month.split("-"))
    total = year * 12 + (m - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _diff_info(curr, prev):
    """Tính chênh lệch và % thay đổi so với tháng trước (chặn lỗi chia cho 0)."""
    diff = curr - prev
    pct = round(diff * 100 / prev, 1) if prev > 0 else None
    return {"diff": diff, "pct": pct}


@bp.route("/")
def dashboard():
    month = _current_month()
    chart = services.spending_by_category(month)
    return render_template(
        "index.html",
        month=month,
        today=date.today().isoformat(),
        categories=Category.query.order_by(Category.type.desc(), Category.name).all(),
        transactions=services.list_transactions(month),
        summary=services.month_summary(month),
        budgets=services.budget_status(month),
        chart_labels=[name for name, _ in chart],
        chart_values=[total for _, total in chart],
    )


@bp.route("/report")
def report():
    month = _current_month()
    prev_month = _shift_month(month, -1)

    summary = services.month_summary(month)
    prev_summary = services.month_summary(prev_month)

    # So sánh Tổng thu, Tổng chi, Còn lại với tháng trước
    comparison = {
        "income": _diff_info(summary["income"], prev_summary["income"]),
        "expense": _diff_info(summary["expense"], prev_summary["expense"]),
        "balance": _diff_info(summary["balance"], prev_summary["balance"]),
    }

    # Bảng chi tiêu theo danh mục (kèm so sánh với tháng trước)
    curr_cats = dict(services.spending_by_category(month))
    prev_cats = dict(services.spending_by_category(prev_month))
    all_names = list(curr_cats.keys()) + [n for n in prev_cats if n not in curr_cats]

    total_expense = summary["expense"]
    category_rows = []
    for name in all_names:
        curr_val = curr_cats.get(name, 0)
        prev_val = prev_cats.get(name, 0)
        category_rows.append({
            "name": name,
            "current": curr_val,
            "previous": prev_val,
            "diff": curr_val - prev_val,
            "share": round(curr_val * 100 / total_expense, 1) if total_expense > 0 else 0,
        })

    # Dữ liệu biểu đồ cột Thu / Chi 6 tháng gần nhất
    trend_months = [_shift_month(month, i) for i in range(-5, 1)]
    trend_labels = [f"{m[5:7]}/{m[:4]}" for m in trend_months]
    trend_income = []
    trend_expense = []
    for m in trend_months:
        s = services.month_summary(m)
        trend_income.append(s["income"])
        trend_expense.append(s["expense"])

    return render_template(
        "report.html",
        month=month,
        prev_month=prev_month,
        summary=summary,
        prev_summary=prev_summary,
        comparison=comparison,
        category_rows=category_rows,
        trend_labels=trend_labels,
        trend_income=trend_income,
        trend_expense=trend_expense,
    )


@bp.route("/transactions", methods=["POST"])
def create_transaction():
    month = request.form.get("date", "")[:7]
    try:
        services.add_transaction(
            request.form.get("amount"),
            request.form.get("date"),
            request.form.get("category_id", type=int),
            request.form.get("note", ""),
        )
        flash("Đã thêm giao dịch.", "ok")
    except ValueError as e:
        flash(str(e), "error")
        month = ""
    return redirect(url_for("main.dashboard", month=month or None))


@bp.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_transaction(transaction_id):
    try:
        services.delete_transaction(transaction_id)
        flash("Đã xóa giao dịch.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.dashboard", month=request.form.get("month")))


@bp.route("/budgets", methods=["POST"])
def create_budget():
    month = request.form.get("month")
    try:
        services.set_budget(request.form.get("category_id", type=int), month, request.form.get("limit"))
        flash("Đã lưu ngân sách.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.dashboard", month=month))