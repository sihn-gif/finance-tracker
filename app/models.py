"""Data model: Category, Transaction, Budget.

Money is stored as an integer number of VND (no float rounding errors).
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # "income" or "expense"


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)  # always > 0
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(200), default="")
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    category = db.relationship("Category")


class Budget(db.Model):
    __table_args__ = (db.UniqueConstraint("category_id", "month"),)

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # "YYYY-MM"
    limit_amount = db.Column(db.Integer, nullable=False)
    category = db.relationship("Category")
