from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tshirt_store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

# تأكد من وجود مجلد التحميلات
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'designs'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'custom'), exist_ok=True)

db = SQLAlchemy(app)

# نماذج قاعدة البيانات
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, default=True)  # إذا كان تصميم افتراضي أو تم رفعه من قبل المستخدم
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # لتصاميم المستخدمين
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    sizes = db.Column(db.Text, nullable=False)  # تخزين كقائمة JSON
    colors = db.Column(db.Text, nullable=False)  # تخزين كقائمة JSON
    material = db.Column(db.String(100), nullable=True)
    in_stock = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # يمكن أن يكون طلب بدون حساب
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # فودافون كاش، عند الاستلام
    payment_status = db.Column(db.String(20), default='pending')  # مدفوع، قيد الانتظار، ملغي
    order_status = db.Column(db.String(20), default='pending')  # قيد المعالجة، تم الشحن، تم التسليم، ملغي
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    design_id = db.Column(db.Integer, db.ForeignKey('design.id'), nullable=True)
    custom_design_path = db.Column(db.String(255), nullable=True)  # إذا كان المستخدم رفع تصميم مخصص
    quantity = db.Column(db.Integer, default=1)
    size = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    design_id = db.Column(db.Integer, db.ForeignKey('design.id'), nullable=True)
    custom_design_path = db.Column(db.String(255), nullable=True)  # إذا كان المستخدم رفع تصميم مخصص
    quantity = db.Column(db.Integer, default=1)
    size = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(20), nullable=False)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# دوال مساعدة
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_or_create_cart():
    cart_id = session.get('cart_id')
    if cart_id:
        cart = Cart.query.filter_by(session_id=cart_id).first()
        if cart:
            return cart
    
    # إنشاء عربة تسوق جديدة
    session_id = str(uuid.uuid4())
    cart = Cart()
    cart.session_id = session_id
    
    # ربط العربة بالمستخدم إذا كان مسجلاً
    if 'user_id' in session:
        cart.user_id = session['user_id']
    
    db.session.add(cart)
    db.session.commit()
    session['cart_id'] = session_id
    return cart

# الصفحة الرئيسية
@app.route('/')
def index():
    featured_products = Product.query.filter_by(featured=True).limit(8).all()
    return render_template('index.html', products=featured_products)

# صفحة المنتجات
@app.route('/products')
def products():
    products = Product.query.all()
    title = "جميع المنتجات"
    
    return render_template('products.html', products=products, title=title)

# صفحة تفاصيل المنتج
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    designs = Design.query.filter_by(is_default=True).all()
    sizes = json.loads(product.sizes)
    colors = json.loads(product.colors)
    return render_template('product_detail.html', product=product, designs=designs, sizes=sizes, colors=colors)

# إضافة منتج إلى سلة التسوق
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    design_id = request.form.get('design_id', type=int)
    size = request.form.get('size')
    color = request.form.get('color')
    quantity = request.form.get('quantity', 1, type=int)
    
    custom_design_path = None
    
    # Handle merged image upload from client
    merged_image_data = request.form.get('merged_image_data')
    if merged_image_data:
        import base64
        import re
        from io import BytesIO
        from PIL import Image
        
        # Extract base64 data
        imgstr = re.search(r'base64,(.*)', merged_image_data).group(1)
        imgdata = base64.b64decode(imgstr)
        
        # Save image
        unique_filename = f"{uuid.uuid4().hex}_merged.jpg"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'custom', unique_filename)
        image = Image.open(BytesIO(imgdata))
        image.save(save_path, 'JPEG')
        
        custom_design_path = f"uploads/custom/{unique_filename}"
    
    # Handle normal custom design upload without merging
    elif 'custom_design' in request.files:
        file = request.files['custom_design']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'custom', unique_filename)
            file.save(file_path)
            custom_design_path = f"uploads/custom/{unique_filename}"
    
    cart = get_or_create_cart()
    
    # التحقق من وجود نفس المنتج بنفس المواصفات في السلة
    existing_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_id=product_id,
        design_id=design_id,
        custom_design_path=custom_design_path,
        size=size,
        color=color
    ).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart_item = CartItem()
        cart_item.cart_id = cart.id
        cart_item.product_id = product_id
        cart_item.design_id = design_id
        cart_item.custom_design_path = custom_design_path
        cart_item.quantity = quantity
        cart_item.size = size
        cart_item.color = color
        db.session.add(cart_item)
    
    db.session.commit()
    flash('تمت إضافة المنتج إلى سلة التسوق بنجاح', 'success')
    return redirect(url_for('cart'))

# صفحة سلة التسوق
@app.route('/cart')
def cart():
    cart = get_or_create_cart()
    cart_items = []
    total = 0
    
    for item in cart.items:
        product = Product.query.get(item.product_id)
        design = None
        if item.design_id:
            design = Design.query.get(item.design_id)
        
        item_data = {
            'id': item.id,
            'product': product,
            'design': design,
            'custom_design_path': item.custom_design_path,
            'quantity': item.quantity,
            'size': item.size,
            'color': item.color,
            'subtotal': product.price * item.quantity
        }
        cart_items.append(item_data)
        total += item_data['subtotal']
    
    return render_template('cart.html', cart_items=cart_items, total=total)

# حذف منتج من سلة التسوق
@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = get_or_create_cart()
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('تم حذف المنتج من سلة التسوق', 'success')
    
    return redirect(url_for('cart'))

# صفحة الدفع
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = get_or_create_cart()
    
    # التحقق من عدم وجود عربة تسوق فارغة
    if not cart.items:
        flash('سلة التسوق فارغة', 'error')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        # معالجة الطلب
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        payment_method = request.form.get('payment_method')
        
        # حساب المبلغ الإجمالي
        total_amount = 0
        for item in cart.items:
            product = Product.query.get(item.product_id)
            total_amount += product.price * item.quantity
        
        # إنشاء رقم طلب فريد
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # إنشاء الطلب
        order = Order()
        order.order_number = order_number
        order.user_id = session.get('user_id')
        order.name = name
        order.phone = phone
        order.address = address
        order.total_amount = total_amount
        order.payment_method = payment_method
        db.session.add(order)
        db.session.flush()  # لتوليد الـ ID قبل إضافة العناصر
        
        # إضافة عناصر الطلب
        for item in cart.items:
            product = Product.query.get(item.product_id)
            order_item = OrderItem()
            order_item.order_id = order.id
            order_item.product_id = item.product_id
            order_item.design_id = item.design_id
            order_item.custom_design_path = item.custom_design_path
            order_item.quantity = item.quantity
            order_item.size = item.size
            order_item.color = item.color
            order_item.unit_price = product.price if product else 0
            db.session.add(order_item)
        
        # حذف العناصر من سلة التسوق
        for item in cart.items:
            db.session.delete(item)
        
        db.session.commit()
        
        # توجيه إلى صفحة تأكيد الطلب
        flash('تم إنشاء طلبك بنجاح!', 'success')
        return redirect(url_for('order_confirmation', order_number=order_number))
    
    # حساب إجمالي سلة التسوق
    cart_items = []
    total = 0
    
    for item in cart.items:
        product = Product.query.get(item.product_id)
        subtotal = product.price * item.quantity
        cart_items.append({
            'product': product,
            'quantity': item.quantity,
            'size': item.size,
            'color': item.color,
            'subtotal': subtotal
        })
        total += subtotal
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

# صفحة تأكيد الطلب
@app.route('/order_confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('order_confirmation.html', order=order)

# صفحة من نحن
@app.route('/about')
def about():
    return render_template('about.html')

# صفحة اتصل بنا
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        contact = Contact()
        contact.name = name
        contact.email = email
        contact.phone = phone
        contact.message = message
        db.session.add(contact)
        db.session.commit()
        
        flash('تم إرسال رسالتك بنجاح، سنتواصل معك قريبًا', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# صفحة حسابي (تتطلب تسجيل الدخول)
@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('account.html', user=user, orders=orders)

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            
            # تحديث عربة التسوق بمعرف المستخدم
            cart = get_or_create_cart()
            cart.user_id = user.id
            db.session.commit()
            
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('index'))
        else:
            flash('فشل تسجيل الدخول. يرجى التحقق من بريدك الإلكتروني وكلمة المرور', 'error')
    
    return render_template('login.html')

# صفحة التسجيل
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # التحقق من عدم وجود المستخدم
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('البريد الإلكتروني مسجل بالفعل', 'error')
            return redirect(url_for('register'))
        
        # إنشاء مستخدم جديد
        hashed_password = generate_password_hash(password or '')
        user = User()
        user.name = name
        user.email = email
        user.password = hashed_password
        user.phone = phone
        user.address = address
        db.session.add(user)
        db.session.commit()
        
        # تسجيل الدخول تلقائيًا
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['is_admin'] = user.is_admin
        
        # تحديث عربة التسوق بمعرف المستخدم
        cart = get_or_create_cart()
        cart.user_id = user.id
        db.session.commit()
        
        flash('تم التسجيل بنجاح!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

# صفحة لوحة التحكم (للمدير فقط)
@app.route('/admin')
def admin_dashboard():
    if 'is_admin' not in session or not session['is_admin']:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('index'))
    
    products_count = Product.query.count()
    orders_count = Order.query.count()
    users_count = User.query.count()
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          products_count=products_count,
                          orders_count=orders_count, 
                          users_count=users_count,
                          recent_orders=recent_orders)

# إدارة المنتجات (للمدير فقط)
@app.route('/admin/products')
def admin_products():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

# إضافة منتج جديد (للمدير فقط)
@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price', type=float)
        sizes = request.form.getlist('sizes')
        colors = request.form.getlist('colors')
        material = request.form.get('material')
        featured = 'featured' in request.form
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                image_path = f"uploads/{unique_filename}"
        
        product = Product(
            name=name,
            description=description,
            price=price,
            image_path=image_path,
            sizes=json.dumps(sizes),
            colors=json.dumps(colors),
            material=material,
            featured=featured
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html')

# تحديث منتج (للمدير فقط)
@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price', type=float)
        product.sizes = json.dumps(request.form.getlist('sizes'))
        product.colors = json.dumps(request.form.getlist('colors'))
        product.material = request.form.get('material')
        product.in_stock = 'in_stock' in request.form
        product.featured = 'featured' in request.form
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # حذف الصورة القديمة إذا وجدت
                if product.image_path:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path.replace('uploads/', ''))
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                product.image_path = f"uploads/{unique_filename}"
        
        db.session.commit()
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    sizes = json.loads(product.sizes)
    colors = json.loads(product.colors)
    
    return render_template('admin/edit_product.html', product=product, sizes=sizes, colors=colors)

# حذف منتج (للمدير فقط)
@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    flash('تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('admin_products'))

# إدارة التصاميم (للمدير فقط)
@app.route('/admin/designs')
def admin_designs():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    designs = Design.query.filter_by(is_default=True).all()
    return render_template('admin/designs.html', designs=designs)

# إضافة تصميم جديد (للمدير فقط)
@app.route('/admin/add_design', methods=['GET', 'POST'])
def admin_add_design():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'designs', unique_filename)
                file.save(file_path)
                image_path = f"uploads/designs/{unique_filename}"
        
        design = Design()
        design.name = name
        design.description = description
        design.image_path = image_path
        design.is_default = True
        
        db.session.add(design)
        db.session.commit()
        
        flash('تم إضافة التصميم بنجاح', 'success')
        return redirect(url_for('admin_designs'))
    
    return render_template('admin/add_design.html')

# إدارة الطلبات (للمدير فقط)
@app.route('/admin/orders')
def admin_orders():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

# تفاصيل الطلب (للمدير فقط)
@app.route('/admin/order/<int:order_id>')
def admin_order_detail(order_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

# تحديث حالة الطلب (للمدير فقط)
@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    order.order_status = request.form.get('order_status')
    order.payment_status = request.form.get('payment_status')
    
    db.session.commit()
    flash('تم تحديث حالة الطلب بنجاح', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))

# إنشاء قاعدة البيانات وإضافة بيانات أولية
@app.route('/setup')
def setup():
    db.create_all()
    
    # التحقق من وجود مدير
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        hashed_password = generate_password_hash('admin123')
        admin = User()
        admin.name = 'مدير النظام'
        admin.email = 'admin@example.com'
        admin.password = hashed_password
        admin.is_admin = True
        db.session.add(admin)
    
    db.session.commit()
    
    flash('تم إعداد قاعدة البيانات بنجاح', 'success')
    return redirect(url_for('index'))

@app.route('/design_yourself')
def design_yourself():
    return render_template('design_yourself.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
