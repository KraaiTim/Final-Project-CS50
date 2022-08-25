from helpers import table_required, employee_login_required, usd
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import mkdtemp
from flask_session import Session
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_enum import EnumField

import enum
import os
from datetime import datetime

# Configure application
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + \
    os.path.join(basedir, 'restuarant.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['JSON_SORT_KEYS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Ensure templates are auto-reloaded for development
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


##### Database classes #####
class Employee(db.Model):
    __tablename__ = 'Employees'
    employee_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    password = db.Column(db.String(20))
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship(
        'Order', backref=db.backref('employee', lazy='joined'))


class OrderStatus(enum.Enum):
    ordered = "Ordered"
    paid = "Paid"


class Order(db.Model):
    __tablename__ = 'Orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float)
    table_id = db.Column(db.Integer, db.ForeignKey(
        'Tables.table_id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey(
        'Employees.employee_id'), nullable=False)
    order_status = db.Column(db.Enum(OrderStatus))


class LineStatus(enum.Enum):
    ordered = "Ordered"
    served = "Served"
    paid = "Paid"


class OrderLine(db.Model):
    __tablename__ = 'OrderLine'
    order_line_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True)
    quantity = db.Column(db.Integer)
    line_remark = db.Column(db.String(100))
    line_status = db.Column(db.Enum(LineStatus))
    order_id = db.Column(db.Integer, db.ForeignKey(
        'Orders.order_id'))
    order = db.relationship('Order', backref="order")
    product_id = db.Column(db.Integer, db.ForeignKey(
        'Products.product_id'))


class Table(db.Model):
    __tablename__ = 'Tables'
    table_id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(20))
    orders = db.relationship(
        'Order', backref=db.backref('table', lazy='joined'))


class Product(db.Model):
    __tablename__ = 'Products'
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50))
    description = db.Column(db.String(250))
    price = db.Column(db.Float)
    order_lines = db.relationship(
        'OrderLine', backref=db.backref('product', lazy='joined'))

###### Marshmellow classes ######


class EmployeeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Employee

    # Fields to expose
    employee_id = ma.auto_field()
    first_name = ma.auto_field()
    last_name = ma.auto_field()


class ProductSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Product

    # Fields to expose
    product_id = ma.auto_field()
    product_name = ma.auto_field()
    description = ma.auto_field()
    price = ma.auto_field()


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


class TableSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Table

    # Fields to expose
    table_id = ma.auto_field()
    table_name = ma.auto_field()


table_schema = TableSchema()
tables_schema = TableSchema(many=True)


class OrderLineSchema(ma.SQLAlchemySchema):
    class Meta:
        model = OrderLine
        ordered = True

    # Fields to expose
    order_line_id = ma.auto_field()
    quantity = ma.auto_field()
    line_remark = ma.auto_field()
    line_status = EnumField(LineStatus, by_value=True)
    product = ma.Nested(ProductSchema)


order_line_schema = OrderLineSchema()
order_lines_schema = OrderLineSchema(many=True)


class OrderSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Order
        ordered = True

    # Fields to expose
    order_id = ma.auto_field()
    order_date = ma.auto_field()
    total_price = ma.auto_field()
    table = ma.Nested(TableSchema)
    employee = ma.Nested(EmployeeSchema)
    order_status = EnumField(OrderStatus, by_value=True)
    order_lines = ma.Nested(order_lines_schema, attribute='order')


order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


##### Flask cli database command #####
@ app.cli.command('create_db')
def create_db():
    db.create_all()
    print("Database created!")


@ app.cli.command('drop_db')
def drop_db():
    db.drop_all()
    print("Database dropped!")


@ app.cli.command('seed_db')
def seed_db():
    testemployee = Employee(first_name="admin",
                            last_name="admin",
                            password=generate_password_hash("admin"),
                            creation_date=datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second))

    testtable = Table(table_name="Test table")

    testproduct1 = Product(product_name="Test product 1",
                           description="Nice test product 1",
                           price=1.01)

    testproduct2 = Product(product_name="Test product 2",
                           description="Nice test product 2",
                           price=2.02)

    db.session.add(testproduct1)
    db.session.add(testproduct2)
    db.session.add(testtable)
    db.session.add(testemployee)

    db.session.commit()

    print("Database seeded!")

##### Routes #####


@ app.route("/products/")
@ employee_login_required
def products():
    products = products_schema.dump(Product.query.all())
    return render_template("products.html", products=products, page_title="Products")


@ app.route("/addproduct", methods=["POST"])
@ employee_login_required
def addproduct():
    if request.method == "POST":
        product_name = request.form.get("product_name")
        description = request.form.get("product_description")
        price = request.form.get("product_price")
        product = Product(product_name=product_name,
                          description=description,
                          price=price)
        db.session.add(product)
        db.session.commit()
        return redirect("/products/")
    else:
        return redirect("/products")


@ app.route("/tables/")
def tables():
    session["table_id"] = None
    tables = tables_schema.dump(Table.query.all())
    return render_template("tables.html", tables=tables)


@ app.route("/addtable", methods=["POST"])
@ employee_login_required
def addtable():
    if request.method == "POST":
        table_name = request.form.get("table_name")
        table = Table(table_name=table_name)
        db.session.add(table)
        db.session.commit()
        return redirect("/tables/")
    else:
        return redirect("/tables")


@app.route("/removetable/", methods=["POST"])
def removetable():
    table_id = request.form.get("id")
    Table.query.filter_by(table_id=table_id).delete()
    db.session.commit()
    return redirect("/tables")


@ app.route("/table/<table_id>", methods=["GET"])
def table(table_id: int):
    table = db.session.query(Table).filter_by(
        table_id=table_id).first()
    # Create session by setting table id
    if table is not None:
        session["table_id"] = table_id
        session["table_name"] = table.table_name
        return render_template("table_overview.html", page_title="Welcome!")
    else:
        flash(f"Table number does not exist!")
        return render_template("404.html")


@ app.route("/")
def index():
    """Show list of products and cart"""
    products = products_schema.dump(Product.query.all())

    if session.get('cart') is not None:
        cart = session['cart']
        total = 0
        cart_dict = {}
        for product_id, qty in cart.items():
            product = product_schema.dump(
                Product.query.filter_by(product_id=product_id).first())
            # Createa dictionary with key product_id and the product object with the qty of the product
            cart_dict[product_id] = {"product": product, "qty": qty}
            total = total + (product["price"] * qty)
        return render_template("index.html", products=products, cart=cart_dict, total=total, page_title="Menu")
    else:
        cart_dict = {}
        return render_template("index.html", products=products, cart=cart_dict, total=0, page_title="Menu")


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log employee in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Clear any session data
        if session:
            session.clear()
        firstname = request.form.get("firstname")
        employee = Employee.query.filter_by(first_name=firstname).first()
        # On the returned employee, check if the password is correct
        if employee:
            if check_password_hash(employee.password, request.form.get("password")):
                session["employee_id"] = employee.employee_id

                # Redirect user to home page
                flash(f"Employee '{firstname}' successfully logged in!")
                return redirect(url_for("tables"))
            else:
                return jsonify(message='Incorrect Email or Password'), 401
        else:
            return jsonify(message='Incorrect Email or Password'), 401
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Get employee name
    employee_first_name = Employee.query.filter_by(
        employee_id=session['employee_id']).first().first_name

    # Forget any employee_id & table_id
    session.clear()

    flash(
        f"Employee '{employee_first_name}' successfully logged out! Please log in")
    # Redirect employee to login form
    return redirect("/login")


@ app.route("/register", methods=["GET", "POST"])
@ employee_login_required
def register():
    """Register employee"""
    if request.method == "POST":
        firstname = request.form.get("firstname")
        employee = Employee.query.filter_by(first_name=firstname).first()
        if employee:
            # An employee with that first name already exists in the database
            return jsonify(message='An employee with this emailaddress already exists'), 409
        else:
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            password = request.form.get("password")
            hashed_password = generate_password_hash(password)
            employee = Employee(first_name=first_name,
                                last_name=last_name, password=hashed_password)
            db.session.add(employee)
            db.session.commit()

            # Redirect user to home page
            flash(f"Employee successfully registered! Please log in")
            return redirect("/login")
    else:
        return render_template("register.html")


@ app.route("/clearcart", methods=["POST"])
def clearcart():
    session['cart'] = None
    return redirect("/")


@ app.route("/addtocart", methods=["POST"])
@ table_required
def addtocart():
    product_id = request.form.get("id")
    if session.get('cart') is not None:
        cart = session['cart']
        # If the product is already in the cart
        if product_id in cart.keys():
            cart[product_id] += 1
        else:
            cart[product_id] = 1
        session['cart'] = cart
    else:
        session['cart'] = {product_id: 1}
    return redirect("/")


@ app.route("/removefromcart", methods=["POST"])
@ table_required
def removefromcart():
    product_id = request.form.get("id")
    if session.get('cart') is not None:
        cart = session['cart']
        if product_id in cart.keys():
            del cart[product_id]
        session['cart'] = cart
    return redirect("/")


@ app.route("/placeorder", methods=["POST"])
@ table_required
def placeorder():
    if session.get('cart') is not None:
        # If no unpaid order exists for this table, create a new one
        order = Order.query.filter_by(
            order_status=OrderStatus.ordered, table_id=session["table_id"]).first()
        if order is None:
            # Retrieve table object
            if "employee_id" in session:
                employee = Employee.query.filter_by(
                    employee_id=session["employee_id"]).first()
            else:
                employee = Employee.query.filter_by(
                    employee_id=1).first()
            table = Table.query.filter_by(
                table_id=session["table_id"]).first()

            # Create cart variable with the dictionary of the cart
            cart = session["cart"]

            # Create order with reference to the table
            order_total_price = 0
            order = Order(order_date=datetime.strptime(str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f'),
                          total_price=order_total_price,
                          table=table,
                          employee=employee,
                          order_status=OrderStatus.ordered)
            db.session.add(order)

            # For loop to create the order lines with reference to product & order
            for product_id in cart.keys():
                product = Product.query.filter_by(
                    product_id=product_id).first()
                line = OrderLine(quantity=cart[product_id],
                                 line_status=LineStatus.ordered,
                                 order=order,
                                 product=product)
                db.session.add(line)

                # Calculate total price of all order lines
                order_total_price = order_total_price + \
                    (product.price * cart[product_id])

                order.total_price = order_total_price

        # An unpaid order exists already for this table
        else:
            order_total_price = order.total_price
            # Create cart variable with the dictionary of the cart
            cart = session["cart"]

            # For loop to create the order lines with reference to product & order
            for product_id in cart.keys():
                product = Product.query.filter_by(
                    product_id=product_id).first()
                line = OrderLine(quantity=cart[product_id],
                                 line_status=LineStatus.ordered,
                                 order=order,
                                 product=product)
                db.session.add(line)

                # Calculate total price of all order lines
                order_total_price = order_total_price + \
                    (product.price * cart[product_id])

            order.total_price = order_total_price
        db.session.commit()

        # Set session["cart"] = None to clear cart
        session["cart"] = None

        return redirect("/order")
    else:
        return redirect("/")


@ app.route("/order/", methods=["GET", "POST"])
@ table_required
def order():
    if request.method == "POST":
        pass
    else:
        order = Order.query.filter_by(
            order_status=OrderStatus.ordered, table_id=session["table_id"]).first()
        order_serialized = order_schema.dump(order)
        return render_template("order.html", order=order_serialized, page_title="Order overview")


@ app.route("/payorder", methods=["POST"])
@ table_required
def payorder():
    # Set status to paid
    if request.method == "POST":
        order_id = request.form.get("id")
        order = Order.query.filter_by(order_id=order_id).first()
        order.order_status = OrderStatus.paid
        db.session.commit()
        return render_template("payment_sucessful.html", page_title="Payment status")


if __name__ == '__main__':
    app.run(debug=True)
