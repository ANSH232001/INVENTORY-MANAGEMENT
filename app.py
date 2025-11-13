from flask import Flask, render_template, request, redirect, url_for
import flask


from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from  datetime import datetime
import pandas as pd
from datetime import date
from flask import make_response
import csv
import io
from datetime import datetime
from flask import jsonify
from flask_migrate import Migrate


#from models import Material, FinishedProduct, Vendor, Invoice, InvoiceItem

import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-very-secure-random-secret-key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)



from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from flask_login import LoginManager, login_user, login_required, logout_user, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # route name for login page

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#CREATING DATABASES

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(50), unique=True, nullable=False)
    material_name = db.Column(db.String(100), nullable=False)
    vendor = db.Column(db.String(100))
    item_category = db.Column(db.String(100))
    unit_of_measurement = db.Column(db.String(50))
    minimum_stock_level = db.Column(db.Integer)
    current_stock = db.Column(db.Integer)
    reorder_quantity = db.Column(db.Integer)
    purchase_history = db.Column(db.Text)
    #material_id = db.Column(db.Integer, db.ForeignKey('material.id', ondelete='CASCADE'), nullable=False)
    yellow_alert = db.Column(db.Integer, nullable=True)
    red_alert = db.Column(db.Integer, nullable=True)

class FinishedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Float(50))
    capacity = db.Column(db.Float(50))
    configuration = db.Column(db.String(100))
    model_name = db.Column(db.String(100))
    dealer_zone = db.Column(db.String(100))
    current_stock = db.Column(db.Integer)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_code = db.Column(db.String(50), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(100))
    address = db.Column(db.String(250))
    gstin = db.Column(db.String(20))
    material_type = db.Column(db.String(100))


class MaterialTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    transaction_type = db.Column(db.String(20),
                                 nullable=False)  # 'purchase', 'return', 'production', 'service', 'rnd', 'other'
    quantity = db.Column(db.Integer, nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    remarks = db.Column(db.String(200))

    material = db.relationship('Material', backref=db.backref('transactions', lazy=True))

class FinishedProductTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    finished_product_id = db.Column(db.Integer, db.ForeignKey('finished_product.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # e.g., 'add', 'update', 'in', 'out'
    quantity = db.Column(db.Integer)
    transaction_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    remarks = db.Column(db.String(200))

    #finished_product = db.relationship('FinishedProduct', backref=db.backref('transactions', lazy=True))

#invoice
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(25), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_gstin = db.Column(db.String(20))
    customer_address = db.Column(db.String(200))
    date = db.Column(db.Date, default=datetime.utcnow)
    subtotal = db.Column(db.Float, default=0.0)
    cgst = db.Column(db.Float, default=0.0)
    sgst = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    rate = db.Column(db.Float)
    gst_rate = db.Column(db.Float)
    line_total = db.Column(db.Float)
    invoice = db.relationship('Invoice', backref=db.backref('items', lazy=True))

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_number = db.Column(db.String(50), unique=True, nullable=False)
    grn_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True)

class PurchaseOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # rate = db.Column(db.Float, nullable=False)
    # total = db.Column(db.Float, nullable=False)

    # Optional: Relationship to Material
    material = db.relationship('Material')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Float(50))
    capacity = db.Column(db.Float(50))
    configuration = db.Column(db.String(100))
    model_name = db.Column(db.String(100))
    current_stock = db.Column(db.Integer)






def generate_material_code():
    last_material = Material.query.order_by(Material.id.desc()).first()
    if last_material and last_material.material_code.startswith('ATPL-'):
        last_num = int(last_material.material_code.split('-')[1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"ATPL-{new_num:04d}"

def generate_grn_number():
    last_po = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
    if last_po and last_po.grn_number.startswith('GRN-'):
        last_num = int(last_po.grn_number.split('-')[1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"GRN-{new_num:05d}"


@app.route('/')
def splash():
    return render_template('intro.html')

from flask import flash

@app.route('/add_purchase_order', methods=['GET', 'POST'])
def add_purchase_order():
    materials = Material.query.all()
    if request.method == 'POST':
        po_number = request.form['purchase_order_number']
        invoice_number = request.form['invoice_number']
        grn_number = request.form['grn_number']
        date_str = request.form['date']
        grn_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_po = PurchaseOrder(
            purchase_order_number=po_number,
            grn_number=grn_number,
            invoice_number=invoice_number,
            date=grn_date
        )
        db.session.add(new_po)
        db.session.flush()

        material_id = int(request.form['material_id'])
        quantity = int(request.form['quantity'])
        if quantity > 0:
            po_item = PurchaseOrderItem(
                purchase_order_id=new_po.id,
                material_id=material_id,
                quantity=quantity
            )
            material = Material.query.get(material_id)
            material.current_stock += quantity
            db.session.add(po_item)

        db.session.commit()
        return redirect(url_for('dashboard'))

    # On GET, generate GRN and current date to populate the form
    generated_grn = generate_grn_number()
    today_date = datetime.today().strftime('%Y-%m-%d')
    return render_template('add_purchase_order.html', materials=materials, generated_grn=generated_grn, today_date=today_date)


@app.route('/modify_material/<int:material_id>', methods=['GET', 'POST'])
def modify_material(material_id):
    material = Material.query.get_or_404(material_id)
    if request.method == 'POST':
        old_data = {
            'material_name': material.material_name,
            'vendor': material.vendor,
            'item_category': material.item_category,
            'unit_of_measurement': material.unit_of_measurement,
            'minimum_stock_level': material.minimum_stock_level,
            'current_stock': material.current_stock,
            'reorder_quantity': material.reorder_quantity,
            'purchase_history': material.purchase_history,
            'yellow_alert': material.yellow_alert,
            'red_alert': material.red_alert
        }

        # Update fields
        material.material_name = request.form['material_name']
        material.vendor = request.form['vendor']
        material.item_category = request.form['item_category']
        material.unit_of_measurement = request.form['unit_of_measurement']
        material.minimum_stock_level = int(request.form['minimum_stock_level'])
        material.current_stock = int(request.form['current_stock'])
        material.reorder_quantity = int(request.form['reorder_quantity'])
        material.purchase_history = request.form['purchase_history']

        yellow_val = request.form.get('yellow_alert')
        red_val = request.form.get('red_alert')
        material.yellow_alert = int(yellow_val) if yellow_val and yellow_val.isdigit() else None
        material.red_alert = int(red_val) if red_val and red_val.isdigit() else None

        db.session.commit()

        # Create a transaction log for modification
        remarks = "Material details modified"
        # Optional: add changed field names
        changes = []
        for key, old_value in old_data.items():
            new_value = getattr(material, key)
            if old_value != new_value:
                changes.append(f"{key}: {old_value} → {new_value}")
        if changes:
            remarks += " [" + "; ".join(changes) + "]"

        transaction = MaterialTransaction(
            material_id=material.id,
            transaction_type='modify',
            quantity=0,  # Or you can use None if allowed
            transaction_date=datetime.today(),
            remarks=remarks
        )
        db.session.add(transaction)
        db.session.commit()

        return redirect(url_for('show_materials'))

    return render_template('modify_material.html', material=material)

@app.route('/delete_material/<int:id>', methods=['POST'])
@login_required
def delete_material(id):
    material = Material.query.get_or_404(id)
    try:
        MaterialTransaction.query.filter_by(material_id=material.id).delete()
        db.session.delete(material)
        db.session.commit()
        flash('Material deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete material.', 'danger')
    return redirect(url_for('show_materials'))

@app.route('/delete_finished_product/<int:id>', methods=['POST'])
@login_required
def delete_finished_product(id):
    product = FinishedProduct.query.get_or_404(id)
    try:
        FinishedProductTransaction.query.filter_by(finished_product_id=product.id).delete()
        db.session.delete(product)
        db.session.commit()
        flash('Finished product deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete finished product.', 'danger')
    return redirect(url_for('show_finished_goods'))

@app.route('/delete_vendor/<int:id>', methods=['POST'])
@login_required
def delete_vendor(id):
    vendor = Vendor.query.get_or_404(id)
    try:
        db.session.delete(vendor)
        db.session.commit()
        flash('Vendor deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete vendor.', 'danger')
    return redirect(url_for('show_vendors'))



@app.route('/dashboard')
def dashboard():
    material_count = Material.query.count()
    finished_product_count = FinishedProduct.query.count()
    vendor_count = Vendor.query.count()
    invoice_count = Invoice.query.count()
    purchase_order_count = PurchaseOrder.query.count()
    customer_count = Customer.query.count()
    recent_purchase_orders = PurchaseOrder.query.order_by(PurchaseOrder.date.desc()).limit(5).all()

    return render_template('dashboard.html',
                           material_count=material_count,
                           finished_product_count=finished_product_count,
                           vendor_count=vendor_count,
                           customer_count=customer_count,
                           invoice_count=invoice_count,
                           purchase_order_count=purchase_order_count,
                           recent_purchase_orders=recent_purchase_orders)


#INVOICE GENERATION
@app.route('/generate_invoice', methods=['GET', 'POST'])
def generate_invoice():
    products = FinishedProduct.query.all()

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_gstin = request.form.get('customer_gstin', '')
        customer_address = request.form.get('customer_address', '')

        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_invoice = Invoice(
            invoice_number=invoice_number,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            customer_address=customer_address
        )
        db.session.add(new_invoice)
        db.session.flush()

        subtotal, cgst_total, sgst_total = 0, 0, 0
        product_names = request.form.getlist('product')
        quantities = request.form.getlist('quantity')

        for pname, qty in zip(product_names, quantities):
            product = FinishedProduct.query.filter_by(name=pname).first()
            if not product or int(qty) <= 0:
                continue
            rate = float(product.capacity) if product.capacity else 0.0
            tax_rate = 18.0
            taxable = int(qty) * rate
            gst = taxable * tax_rate / 100
            line_total = taxable + gst
            subtotal += taxable
            cgst_total += gst / 2
            sgst_total += gst / 2

            db.session.add(InvoiceItem(
                invoice_id=new_invoice.id,
                product_name=pname,
                quantity=int(qty),
                rate=rate,
                gst_rate=tax_rate,
                line_total=line_total
            ))

        new_invoice.subtotal = subtotal
        new_invoice.cgst = cgst_total
        new_invoice.sgst = sgst_total
        new_invoice.total = subtotal + cgst_total + sgst_total
        db.session.commit()
        return redirect(url_for('view_invoice', invoice_id=new_invoice.id))

    return render_template('generate_invoice.html', products=products)


@app.route('/view_invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoice.html', invoice=invoice)


# DASHBOARD ALERTS API
@app.route('/dashboard_alerts')
def dashboard_alerts():
    low_stock_count = Material.query.filter(Material.current_stock < Material.minimum_stock_level).count()
    pending_invoice_count = Invoice.query.filter(Invoice.total == 0).count() if 'invoice' in db.metadata.tables else 0
    return jsonify({'low_stock': low_stock_count, 'pending_invoices': pending_invoice_count})


@app.route('/invoice_history')
def invoice_history():
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template('invoice_history.html', invoices=invoices)


@app.route('/add_material', methods=['GET', 'POST'])
@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        material_code  = generate_material_code()
        material = Material(
            material_code=request.form['material_code'],
            material_name=request.form['material_name'],
            vendor=request.form['vendor'],
            item_category=request.form['item_category'],
            unit_of_measurement=request.form['unit_of_meas urement'],
            minimum_stock_level=int(request.form['minimum_stock_level']),
            current_stock=int(request.form['current_stock']),
            reorder_quantity=int(request.form['reorder_quantity']),
            purchase_history=request.form['purchase_history']
        )
        db.session.add(material)
        db.session.commit()

        transaction = MaterialTransaction(
            material_id=material.id,
            transaction_type='add',
            quantity=material.current_stock,
            transaction_date=datetime.today(),
            remarks='Material IN'
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('dashboard'))
    next_code = generate_material_code()
    return render_template('add_materials.html', material_code= next_code)




# Assuming you have a list for products
finished_goods_list = []

@app.route('/add_finished_product', methods=['GET', 'POST'])
def add_finished_product():
    if request.method == 'POST':
        product_code = request.form['product_code']

        # Check if product_code already exists
        existing_product = FinishedProduct.query.filter_by(product_code=product_code).first()
        if existing_product:
            return "Product code already exists! Please use a unique code.", 400
        product = FinishedProduct(
            product_code=request.form['product_code'],
            name=request.form['name'],
            capacity=request.form['capacity'],
            configuration=request.form['configuration'],
            model_name=request.form['model_name'],
            dealer_zone=request.form['dealer_zone'],
            current_stock=int(request.form['current_stock']),
            rate = float(request.form['rate'])
        )
        db.session.add(product)
        db.session.commit()      # Get product.id assigned before commit


            # other fields...


        transaction = FinishedProductTransaction(
            finished_product_id=product.id,
            transaction_type='add',
            quantity=product.current_stock,
            transaction_date=datetime.today(),
            remarks='Finished goods  IN'
        )
        db.session.add(transaction)
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('add_finished_product.html')

@app.route('/show_materials')
def show_materials():
    materials = Material.query.all()  # Fetch data from DB
    materials_with_alert = []
    for m in materials:
        # If alert thresholds are not set, do not color or set default 'sufficient'
        if m.red_alert is not None and m.current_stock < m.red_alert:
            alert = 'red'
        elif m.yellow_alert is not None and m.current_stock < m.yellow_alert:
            alert = 'yellow'
        else:
            alert = 'sufficient'
        materials_with_alert.append((m,alert))

    return render_template('show_materials.html', materials=materials_with_alert)

@app.route('/show_finished_goods')
def show_finished_goods():
    products = FinishedProduct.query.all()
    return render_template('show_finished_goods.html', products=products)



@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query')
    materials = []
    products = []
    if query:
        # Case-insensitive search by code or name in materials
        materials = Material.query.filter(
            (Material.material_code.ilike(f'%{query}%')) |
            (Material.material_name.ilike(f'%{query}%'))
        ).all()
        # Case-insensitive search by code or name in products
        products = FinishedProduct.query.filter(
            (FinishedProduct.product_code.ilike(f'%{query}%')) |
            (FinishedProduct.name.ilike(f'%{query}%'))
        ).all()

    return render_template('search.html', query=query, materials=materials, products=products)

@app.route('/material_transaction', methods=['GET', 'POST'])
def material_transaction():
    materials = Material.query.all()
    if request.method == 'POST':
        material_id = int(request.form['material_id'])
        transaction_type = request.form['transaction_type']
        quantity = int(request.form['quantity'])
        remarks = request.form['remarks']
        transaction_date_str = request.form['transaction_date']
        transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()

        transaction = MaterialTransaction(
            material_id=material_id,
            transaction_type=transaction_type,
            quantity=quantity,
            transaction_date=transaction_date,
            remarks=remarks
        )
        db.session.add(transaction)
        db.session.commit()
        # Optional: Update current stock accordingly or handle in reconciliation
        return redirect(url_for('material_transaction'))
    return render_template('material_transaction.html', materials=materials)

@app.route('/history')
def history():
    filter_type = request.args.get('type', 'material')

    if filter_type == 'finished_goods':
        # Fetch finished goods transactions with related product data
        records = FinishedProductTransaction.query.join(FinishedProduct).all()
    else:
        # Default to material transactions with material data
        records = MaterialTransaction.query.join(Material).all()

    return render_template('history.html', records=records, filter_type=filter_type)

from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import date
# ... (other imports and configurations)

# Update Material Stock Route
@app.route('/update_material/<int:id>', methods=['GET', 'POST'])
def update_material(id):
    material = Material.query.get_or_404(id)
    if request.method == 'POST':
        try:
            new_stock = int(request.form['current_stock'])
        except ValueError:
            return "Invalid stock quantity", 400
        old_stock = material.current_stock or 0
        material.current_stock = new_stock
        db.session.commit()
        quantity_change = new_stock - old_stock
        if quantity_change != 0:
            transaction_type = 'stock_increase' if quantity_change > 0 else 'stock_decrease'
            transaction = MaterialTransaction(
                material_id=material.id,
                transaction_type=transaction_type,
                quantity=abs(quantity_change),
                transaction_date=date.today(),
                remarks='Stock updated manually'
            )
            db.session.add(transaction)
            db.session.commit()
        return redirect(url_for('show_materials'))
    return render_template('update_material.html', material=material)

# Update Finished Product Stock Route
@app.route('/update_finished_product/<int:id>', methods=['GET', 'POST'])
def update_finished_product(id):
    product = FinishedProduct.query.get_or_404(id)
    if request.method == 'POST':
        try:
            new_stock = int(request.form['current_stock'])
        except ValueError:
            return "Invalid stock quantity", 400
        old_stock = product.current_stock or 0
        product.current_stock = new_stock
        db.session.commit()
        quantity_change = new_stock - old_stock
        if quantity_change != 0:
            transaction_type = 'stock_increase' if quantity_change > 0 else 'stock_decrease'
            transaction = FinishedProductTransaction(
                finished_product_id=product.id,
                transaction_type=transaction_type,
                quantity=abs(quantity_change),
                transaction_date=date.today(),
                remarks='Stock updated manually'
            )
            db.session.add(transaction)
            db.session.commit()
        return redirect(url_for('show_finished_goods'))
    return render_template('update_finished_product.html', product=product)

@app.route('/add_vendor', methods=['GET', 'POST'])
def add_vendor():
    if request.method == 'POST':
        vendor_code = request.form['vendor_code']
        company_name = request.form['company_name']
        contact = request.form['contact']
        address = request.form['address']
        gstin = request.form['gstin']
        material_type = request.form['material_type']

        vendor = Vendor(
            vendor_code=vendor_code,
            company_name=company_name,
            contact=contact,
            address=address,
            gstin=gstin,
            material_type=material_type
        )
        db.session.add(vendor)
        db.session.commit()
        return redirect(url_for('show_vendors'))

    return render_template('add_vendor.html')
@app.route('/show_vendors')
def show_vendors():
    vendors = Vendor.query.all()
    return render_template('show_vendors.html', vendors=vendors)





@app.route('/export/<string:table_name>')
def export_data(table_name):
    output = io.StringIO()
    writer = csv.writer(output)

    if table_name == 'materials':
        data = Material.query.all()
        writer.writerow(['ID', 'Material Code', 'Material Name', 'Vendor', 'Item Category',
                         'UOM', 'Min Stock', 'Current Stock', 'Reorder Qty', 'Purchase History'])
        for m in data:
            writer.writerow([m.id, m.material_code, m.material_name, m.vendor, m.item_category,
                             m.unit_of_measurement, m.minimum_stock_level, m.current_stock,
                             m.reorder_quantity, m.purchase_history])

    elif table_name == 'finished_products':
        data = FinishedProduct.query.all()
        writer.writerow(['ID', 'Product Code', 'Name', 'Capacity', 'Configuration',
                         'Model Name', 'Dealer Zone', 'Current Stock'])
        for p in data:
            writer.writerow([p.id, p.product_code, p.name, p.capacity, p.configuration,
                             p.model_name, p.dealer_zone, p.current_stock])

    elif table_name == 'vendors':
        data = Vendor.query.all()
        writer.writerow(['ID', 'Vendor Code', 'Company Name', 'Contact', 'Address',
                         'GSTIN', 'Material Type'])
        for v in data:
            writer.writerow([v.id, v.vendor_code, v.company_name, v.contact,
                             v.address, v.gstin, v.material_type])
    else:
        return "Invalid table name", 400

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={table_name}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

from sqlalchemy.exc import IntegrityError

@app.route('/import/<string:table_name>', methods=['GET', 'POST'])
def import_data(table_name):
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            return "No file uploaded", 400 #it will return the written string

        filename = file.filename.lower()

        import pandas as pd
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return "Only .csv or .xlsx files are allowed", 400

        try:
            if table_name == 'materials':
                for _, row in df.iterrows():
                    # Check if material_code already exists
                    existing = Material.query.filter_by(material_code=row.get('material_code') or row.get('Material Code')).first()
                    if existing:
                        # Optionally update existing record here or continue
                        continue

                    new_material = Material(
                        material_code=row.get('material_code') or row.get('Material Code'),
                        material_name=row.get('material_name') or row.get('Material Name'),
                        vendor=row.get('vendor') or row.get('Vendor'),
                        item_category=row.get('item_category') or row.get('Item Category'),
                        unit_of_measurement=row.get('unit_of_measurement') or row.get('Unit Of Measurement'),
                        minimum_stock_level=int(row.get('minimum_stock_level') or row.get('Minimum Stock Level') or 0),
                        current_stock=int(row.get('current_stock') or row.get('Current Stock') or 0),
                        reorder_quantity=int(row.get('reorder_quantity') or row.get('Reorder Quantity') or 0),
                        purchase_history=row.get('purchase_history') or row.get('Purchase History')
                    )
                    db.session.add(new_material)

            elif table_name == 'vendors':
                for _, row in df.iterrows():
                    existing = Vendor.query.filter_by(vendor_code=row.get('vendor_code') or row.get('Vendor Code')).first()
                    if existing:
                        continue
                    new_vendor = Vendor(
                        vendor_code=row.get('vendor_code') or row.get('Vendor Code'),
                        company_name=row.get('company_name') or row.get('Company Name'),
                        contact=row.get('contact') or row.get('Contact'),
                        address=row.get('address') or row.get('Address'),
                        gstin=row.get('gstin') or row.get('GSTIN'),
                        material_type=row.get('material_type') or row.get('Material Type')
                    )
                    db.session.add(new_vendor)

            elif table_name == 'finished_products':
                for _, row in df.iterrows():
                    existing = FinishedProduct.query.filter_by(product_code=row.get('product_code') or row.get('Product Code')).first()
                    if existing:
                        continue
                    new_product = FinishedProduct(
                        product_code=row.get('product_code') or row.get('Product Code'),
                        name=row.get('name') or row.get('Name'),
                        capacity=row.get('capacity') or row.get('Capacity'),
                        configuration=row.get('configuration') or row.get('Configuration'),
                        model_name=row.get('model_name') or row.get('Model Name'),
                        dealer_zone=row.get('dealer_zone') or row.get('Dealer Zone'),
                        current_stock=int(row.get('current_stock') or row.get('Current Stock') or 0)
                    )
                    db.session.add(new_product)

            else:
                return "Invalid table name", 400

            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return "Integrity error: Possible duplicate or invalid data detected.", 400

        return f"{table_name.replace('_', ' ').title()} data imported successfully!"

    return render_template('import.html', table_name=table_name)

ALLOWED_USERNAMES = ['ATPL-25110', 'bob', 'charlie']  # Add authorized usernames here

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in ALLOWED_USERNAMES:
            return "Username not authorized to register", 403
        if User.query.filter_by(username=username).first():
            return "Username already registered", 400
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in ALLOWED_USERNAMES:
            return "Username not authorized to login", 403
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return "Invalid username or password", 400
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/search_materials')
def search_materials():
    query = request.args.get('q', '')
    materials = Material.query.filter(Material.material_name.ilike(f'%{query}%')).all()
    results = [{'id': m.id, 'text': f"{m.material_name} (Stock: {m.current_stock})"} for m in materials]
    return jsonify(results)


from sqlalchemy.exc import IntegrityError


@app.route('/purchase_order', methods=['GET', 'POST'])
def purchase_order():
    materials = Material.query.all()
    if request.method == 'POST':
        po_number = request.form['purchase_order_number']

        # Check uniqueness first
        existing_po = PurchaseOrder.query.filter_by(purchase_order_number=po_number).first()
        if existing_po:
            # Handle duplicate case - return error message or flash message
            return "Purchase Order Number already exists. Please use a unique number.", 400

        invoice_number = request.form['invoice_number']
        grn_number = request.form['grn_number']
        new_po = PurchaseOrder(
            purchase_order_number=po_number,
            invoice_number=invoice_number,
            grn_number=grn_number,
            date=datetime.today()
        )
        db.session.add(new_po)
        db.session.flush()

        material_ids = request.form.getlist('material_id')
        quantities = request.form.getlist('quantity')

        for mid, qty in zip(material_ids, quantities):
            material = Material.query.get(int(mid))
            if material and int(qty) > 0:
                new_po_item = PurchaseOrderItem(
                    purchase_order_id=new_po.id,
                    product_id=material.id,
                    quantity=int(qty)
                )
                material.current_stock += int(qty)
                db.session.add(new_po_item)

        # material_ids = request.form.getlist('material_id')
        # quantities = request.form.getlist('quantity')
        # rates = request.form.getlist('rate')
        # totals = request.form.getlist('total')
        #
        # for mid, qty, rate, total in zip(material_ids, quantities, rates, totals):
        #     qty = int(qty)
        #     rate = float(rate)
        #     total = float(total)
        #     if qty > 0:
        #         po_item = PurchaseOrderItem(
        #             purchase_order_id=new_po.id,
        #             product_id=int(mid),
        #             quantity=qty,
        #             rate=rate,
        #             total=total
        #         )
        #         material = Material.query.get(int(mid))
        #         material.current_stock += qty  # Update stock
        #         db.session.add(po_item)



        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return f"Database error: {str(e)}", 500

        return redirect(url_for('dashboard'))

    return render_template('purchase_order.html', materials=materials)


@app.route('/api/purchase_orders')
def api_purchase_orders():
    pos = PurchaseOrder.query.order_by(PurchaseOrder.date.desc()).all()
    data = []
    for po in pos:
        data.append({
            'id': po.id,
            'purchase_order_number': po.purchase_order_number,
            'grn_number': po.grn_number,
            'invoice_number': po.invoice_number,
            'date': po.date.strftime('%Y-%m-%d'),
            'items': [{
                'product_name': item.material.material_name if item.material else '',
                'quantity': item.quantity
            } for item in po.items]
        })
    return jsonify(data)


@app.route('/customer')
def customer():
    products = FinishedProduct.query.all()
    return render_template('customer.html', products=products)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0",debug=True,port=8080)
