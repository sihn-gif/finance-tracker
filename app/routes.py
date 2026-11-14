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
