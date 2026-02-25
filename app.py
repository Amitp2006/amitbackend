from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False
)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------- MODELS ----------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    amount = db.Column(db.Float)
    user_id = db.Column(db.Integer)
# ---------- ROUTES ----------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Invalid input"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed = generate_password_hash(data["password"])
    user = User(email=data["email"], password=hashed)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "OK"})
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password, data["password"]):
        return jsonify({"user_id": user.id})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/add-expense", methods=["POST"])
def add_expense():
    data = request.json
    expense = Expense(
        title=data["title"],
        amount=data["amount"],
        user_id=data["user_id"]
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify({"message": "Expense added"})

@app.route("/expenses/<int:user_id>")
def get_expenses(user_id):
    expenses = Expense.query.filter_by(user_id=user_id).all()
    return jsonify([
        {"id": e.id, "title": e.title, "amount": e.amount}
        for e in expenses
    ])

@app.route("/update-expense/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.json
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    expense.title = data.get("title", expense.title)
    expense.amount = data.get("amount", expense.amount)

    db.session.commit()
    return jsonify({"message": "Expense updated"})

@app.route("/delete-expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted"})

@app.route("/")
def health_check():
    return "OK"

if __name__ == "__main__":
    app.run(debug=True)