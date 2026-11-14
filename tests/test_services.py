import pytest

from app import create_app, services
from app.models import Category


@pytest.fixture
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True})
    with app.app_context():
        yield app


def cat(name):
    return Category.query.filter_by(name=name).one().id


# ----- validation -----
@pytest.mark.parametrize("bad", [0, -5, "abc", None, ""])
def test_amount_must_be_positive_integer(app, bad):
    with pytest.raises(ValueError):
        services.add_transaction(bad, "2026-11-01", cat("Ăn uống"))


@pytest.mark.parametrize("bad", ["2026-13-01", "01/11/2026", "", None])
def test_invalid_date_rejected(app, bad):
    with pytest.raises(ValueError):
        services.add_transaction(1000, bad, cat("Ăn uống"))


def test_unknown_category_rejected(app):
    with pytest.raises(ValueError):
        services.add_transaction(1000, "2026-11-01", 9999)


# ----- reports -----
def test_empty_month_summary_is_zero(app):
    assert services.month_summary("2026-11") == {"income": 0, "expense": 0, "balance": 0}


def test_month_summary_and_boundaries(app):
    services.add_transaction(10_000_000, "2026-11-01", cat("Lương"))
    services.add_transaction(100_000, "2026-11-30", cat("Ăn uống"))
    services.add_transaction(999_999, "2026-12-01", cat("Ăn uống"))  # tháng sau, không tính
    services.add_transaction(999_999, "2026-10-31", cat("Ăn uống"))  # tháng trước, không tính
    assert services.month_summary("2026-11") == {"income": 10_000_000, "expense": 100_000, "balance": 9_900_000}


def test_december_rolls_over_to_next_year(app):
    services.add_transaction(5000, "2026-12-31", cat("Đi lại"))
    services.add_transaction(7000, "2027-01-01", cat("Đi lại"))
    assert services.month_summary("2026-12")["expense"] == 5000


def test_spending_by_category_sorted(app):
    services.add_transaction(50_000, "2026-11-02", cat("Ăn uống"))
    services.add_transaction(30_000, "2026-11-03", cat("Ăn uống"))
    services.add_transaction(200_000, "2026-11-04", cat("Giải trí"))
    assert services.spending_by_category("2026-11") == [("Giải trí", 200_000), ("Ăn uống", 80_000)]


# ----- budgets -----
@pytest.mark.parametrize("spent,limit,level", [
    (0, 100, "ok"), (79, 100, "ok"), (80, 100, "warning"), (99, 100, "warning"),
    (100, 100, "exceeded"), (150, 100, "exceeded"),
])
def test_budget_levels(spent, limit, level):
    assert services.budget_level(spent, limit) == level


def test_budget_status_reflects_spending(app):
    services.set_budget(cat("Ăn uống"), "2026-11", 1_000_000)
    services.add_transaction(850_000, "2026-11-10", cat("Ăn uống"))
    [status] = services.budget_status("2026-11")
    assert status["percent"] == 85 and status["level"] == "warning"


def test_duplicate_budget_rejected(app):
    services.set_budget(cat("Ăn uống"), "2026-11", 1_000_000)
    with pytest.raises(ValueError):
        services.set_budget(cat("Ăn uống"), "2026-11", 2_000_000)


def test_budget_only_for_expense_categories(app):
    with pytest.raises(ValueError):
        services.set_budget(cat("Lương"), "2026-11", 1_000_000)


def test_delete_transaction(app):
    t = services.add_transaction(1000, "2026-11-01", cat("Ăn uống"))
    services.delete_transaction(t.id)
    assert services.list_transactions("2026-11") == []
    with pytest.raises(ValueError):
        services.delete_transaction(t.id)


def test_dashboard_page_loads(app):
    services.add_transaction(1000, "2026-11-01", cat("Ăn uống"))
    r = app.test_client().get("/?month=2026-11")
    assert r.status_code == 200 and "Sổ chi tiêu".encode() in r.data
