from . import db
from datetime import datetime, timedelta

class User(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default= "user")
    verified = db.Column(db.Boolean, default = False)
    verification_code = db.Column(db.String(6), nullable = True)
    code_expiry = db.Column(db.DateTime, nullable = True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship("Product", backref="category", lazy=True)
    

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    image = db.Column(db.String(200), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)

    def __repr__(self):
        return f"<product {self.name}>"

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"),)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    quantity = db.Column(db.Integer, default=1)

    product = db.relationship("Product")

class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    
    created_at = db.Column(db.DateTime, default=db.func.now())
    order_status = db.Column(db.String(50),default="pending")

    items = db.relationship("OrderItem", backref="order", lazy=True)
    user = db.relationship('User', backref='orders')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("customer_order.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product")

