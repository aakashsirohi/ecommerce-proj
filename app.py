# app.py

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    FloatField,
    SubmitField,
    PasswordField,
    SubmitField,
    StringField,
    PasswordField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config[
    "SECRET_KEY"
] = b"c5f106a29285bf65e7aaf70c971091cd"  # Change this to a random string
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):  # User Schema
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8)]
    )
    confirm_new_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("new_password")]
    )
    submit = SubmitField("Change Password")


class Product(db.Model):  # Product Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    available = db.Column(db.Boolean, nullable=True, default=True)


class ProductForm(FlaskForm):  # Prodcut Form
    name = StringField("Product Name", validators=[DataRequired()])
    description = TextAreaField("Description")
    price = FloatField("Price", validators=[DataRequired()])
    image_url = StringField("Image URL")
    submit = SubmitField("Add Product")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Corrected line
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists. Choose a different one.", "danger")
        else:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully. You can now log in.", "success")
            return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Login failed. Check your username and password.", "danger")

    return render_template("login.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    print("Current user password:", current_user.password)
    print("Entered current password:", form.current_password.data)
    if form.validate_on_submit():
        # Check if the current password provided matches the user's actual password
        if current_user.password == form.current_password.data:
            current_user.password = form.new_password.data
            db.session.commit()
            flash("Your password has been changed successfully.", "success")
            return redirect(url_for("home"))
        else:
            flash("Current password is incorrect.", "danger")

    return render_template("change-password.html", form=form)


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    form = ProductForm()

    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=form.image_url.data,
            available=True,
        )

        db.session.add(new_product)
        db.session.commit()

        flash("Product added successfully!", "success")
        return redirect(url_for("product_list"))

    return render_template("add-product.html", form=form)


@app.route("/products")
@login_required
def product_list():
    products = Product.query.filter_by(available=True)
    return render_template("product.html", products=products)


@app.route("/buy/<int:product_id>", methods=["POST"])
@login_required
def buy_product(product_id):
    product = Product.query.get(product_id)

    if product:
        # Update the product's status or set a flag like product.available = True
        product.available = False
        db.session.commit()

        flash(
            f"Product '{product.name}' moved to products owned successfully.", "success"
        )
    else:
        flash("Product not found.", "error")

    # After performing the logic, redirect to the product_list route
    return redirect(url_for("products_owned_page"))


@app.route("/own/<int:product_id>", methods=["POST"])
@login_required
def owned__product(product_id):
    product = Product.query.get(product_id)

    if product:
        product.available = True
        db.session.commit()

        flash(
            f"Product '{product.name}' moved to products available successfully.",
            "success",
        )
    else:
        flash("Product not found.", "error")

    # After performing the logic, redirect to the product_list route
    return redirect(url_for("product_list"))


@app.route("/products_owned")
@login_required
def products_owned_page():
    products = Product.query.filter_by(available=False)
    return render_template("products-owned.html", products=products)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout successful!", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
