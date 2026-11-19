import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()  # Loads optional settings from a local .env file.

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "cloudcart.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(app.instance_path, exist_ok=True)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


# ----------------------------- DATABASE MODELS -----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    orders = db.relationship("Order", backref="customer", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    stock = db.Column(db.Integer, default=20)
    featured = db.Column(db.Boolean, default=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(40), default="Confirmed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ----------------------------- HELPER FUNCTIONS -----------------------------
def get_cart_items():
    """Read product IDs and quantities from the browser session."""
    cart = session.get("cart", {})
    items, total, count = [], 0, 0

    for product_id, quantity in cart.items():
        product = db.session.get(Product, int(product_id))
        if product and product.stock > 0:
            quantity = min(int(quantity), product.stock)
            subtotal = product.price * quantity
            items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
            total += subtotal
            count += quantity

    return items, total, count


@app.context_processor
def inject_cart_count():
    _, _, count = get_cart_items()
    return {"cart_count": count}


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ----------------------------- STORE ROUTES -----------------------------
@app.route("/")
def home():
    featured = Product.query.filter_by(featured=True).limit(4).all()
    categories = db.session.query(Product.category).distinct().all()
    return render_template("index.html", featured=featured,
                           categories=[c[0] for c in categories])


@app.route("/products")
def products():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    all_categories = [c[0] for c in db.session.query(Product.category).distinct().all()]
    return render_template("products.html", products=query.order_by(Product.name).all(),
                           categories=all_categories, search=search, selected_category=category)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)
    return render_template("product_detail.html", product=product)


@app.route("/cart")
def cart():
    items, total, _ = get_cart_items()
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = db.get_or_404(Product, product_id)
    if product.stock < 1:
        flash("This product is currently out of stock.", "error")
        return redirect(request.referrer or url_for("products"))
    cart_data = session.get("cart", {})
    key = str(product.id)
    cart_data[key] = min(int(cart_data.get(key, 0)) + 1, product.stock)
    session["cart"] = cart_data
    flash(f"{product.name} added to your cart.", "success")
    return redirect(request.referrer or url_for("products"))


@app.post("/cart/update")
def update_cart():
    cart_data = session.get("cart", {})
    for product_id in list(cart_data.keys()):
        try:
            quantity = int(request.form.get(f"quantity_{product_id}", 0))
        except ValueError:
            quantity = 0
        product = db.session.get(Product, int(product_id))
        if not product or quantity <= 0:
            cart_data.pop(product_id, None)
        else:
            cart_data[product_id] = min(quantity, product.stock)
    session["cart"] = cart_data
    flash("Your cart has been updated.", "success")
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    flash("Item removed from your cart.", "info")
    return redirect(url_for("cart"))


# ----------------------------- ACCOUNT ROUTES -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account has been created. Welcome to CloudCart!", "success")
            return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("You are now logged in.", "success")
            return redirect(request.args.get("next") or url_for("home"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ----------------------------- CHECKOUT AND ORDERS -----------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, total, _ = get_cart_items()
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("products"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        postal_code = request.form.get("postal_code", "").strip()
        if not all([full_name, address, city, postal_code]):
            flash("Please complete all delivery fields.", "error")
            return render_template("checkout.html", items=items, total=total)

        order = Order(user_id=current_user.id, full_name=full_name, address=address,
                      city=city, postal_code=postal_code, total=total)
        db.session.add(order)
        for item in items:
            product = item["product"]
            if product.stock < item["quantity"]:
                db.session.rollback()
                flash(f"Not enough stock available for {product.name}.", "error")
                return redirect(url_for("cart"))
            product.stock -= item["quantity"]
            db.session.add(OrderItem(order=order, product_id=product.id,
                                     product_name=product.name,
                                     quantity=item["quantity"], unit_price=product.price))
        db.session.commit()
        session["cart"] = {}
        flash("Order placed! This demo uses simulated payment and no money was charged.", "success")
        return redirect(url_for("order_detail", order_id=order.id))

    return render_template("checkout.html", items=items, total=total)


@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=user_orders)


@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("order_detail.html", order=order)


# ----------------------------- ADMIN ROUTES -----------------------------
@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html", products=Product.query.order_by(Product.id.desc()).all(),
                           orders=Order.query.order_by(Order.created_at.desc()).limit(10).all())


@app.route("/admin/product/new", methods=["GET", "POST"])
@admin_required
def new_product():
    if request.method == "POST":
        try:
            product = Product(
                name=request.form["name"].strip(),
                description=request.form["description"].strip(),
                price=float(request.form["price"]),
                category=request.form["category"].strip(),
                image_url=request.form["image_url"].strip(),
                stock=int(request.form["stock"]),
                featured=bool(request.form.get("featured"))
            )
            if product.price < 0 or product.stock < 0:
                raise ValueError()
            db.session.add(product)
            db.session.commit()
            flash("Product created.", "success")
            return redirect(url_for("admin"))
        except (KeyError, ValueError):
            flash("Please enter valid product details.", "error")
    return render_template("product_form.html", product=None)


@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        try:
            product.name = request.form["name"].strip()
            product.description = request.form["description"].strip()
            product.price = float(request.form["price"])
            product.category = request.form["category"].strip()
            product.image_url = request.form["image_url"].strip()
            product.stock = int(request.form["stock"])
            product.featured = bool(request.form.get("featured"))
            if product.price < 0 or product.stock < 0:
                raise ValueError()
            db.session.commit()
            flash("Product updated.", "success")
            return redirect(url_for("admin"))
        except (KeyError, ValueError):
            flash("Please enter valid product details.", "error")
    return render_template("product_form.html", product=product)


@app.post("/admin/product/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    if OrderItem.query.filter_by(product_id=product.id).first():
        flash("This product is part of an order and cannot be deleted. Set its stock to zero instead.", "error")
    else:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "info")
    return redirect(url_for("admin"))


# ----------------------------- ERROR PAGES -----------------------------
@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page or product could not be found."), 404


# ----------------------------- INITIAL SETUP -----------------------------
def seed_database():
    if Product.query.count() == 0:
        sample_products = [
            ("Aero Wireless Headphones", "Immersive sound, soft ear cushions and long battery life.", 3499, "Electronics", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900", 18, True),
            ("Pulse Smart Watch", "A clean everyday smartwatch with fitness and notification features.", 4999, "Electronics", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900", 12, True),
            ("Everyday Backpack", "A lightweight backpack with organized storage for daily essentials.", 1799, "Lifestyle", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900", 25, True),
            ("Studio Desk Lamp", "Minimal desk lighting for focused work and study sessions.", 1299, "Home", "https://images.unsplash.com/photo-150 나?w=900", 15, False),
            ("Classic Running Shoes", "Comfortable shoes designed for daily movement.", 2999, "Fashion", "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900", 20, True),
            ("Minimal Travel Bottle", "Reusable insulated bottle for work, travel and the gym.", 799, "Lifestyle", "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=900", 30, False),
            ("Mechanical Keyboard", "Tactile typing feel with a compact modern layout.", 2799, "Electronics", "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=900", 10, False),
            ("Ceramic Coffee Mug", "A simple ceramic mug for your everyday coffee break.", 499, "Home", "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=900", 40, False),
        ]
        for name, description, price, category, image_url, stock, featured in sample_products:
            db.session.add(Product(name=name, description=description, price=price,
                                   category=category, image_url=image_url,
                                   stock=stock, featured=featured))
    if not User.query.filter_by(email="admin@cloudcart.local").first():
        admin_user = User(name="CloudCart Admin", email="admin@cloudcart.local", is_admin=True)
        admin_user.set_password(os.environ.get("ADMIN_PASSWORD", "Admin@12345"))
        db.session.add(admin_user)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_database()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
