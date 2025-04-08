import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Application Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tea-order-secret-key'
app.config['SESSION_PERMANENT'] = True  # Kalıcı oturum ayarı
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=90)  # 90 gün sürecek oturum
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", engineio_logger=False)

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
PRICES_FILE = os.path.join(DATA_DIR, 'prices.json')
STOCK_FILE = os.path.join(DATA_DIR, 'stock.json')
COMPUTERS_FILE = os.path.join(DATA_DIR, 'computers.json')
ROOMS_FILE = os.path.join(DATA_DIR, 'rooms.json')
NOTES_FILE = os.path.join(DATA_DIR, 'notes.json')
FREQUENT_ORDERS_FILE = os.path.join(DATA_DIR, 'frequent_orders.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PASSWORDS_FILE = os.path.join(DATA_DIR, 'passwords.json')
ACTIVE_ORDERS_FILE = os.path.join(DATA_DIR, 'active_orders.json')
ORDER_LOG_FILE = os.path.join(DATA_DIR, 'order_log.json')
BALANCE_TRANSFER_LOG_FILE = os.path.join(DATA_DIR, 'balance_transfer_log.json')
BALANCE_ADD_LOG_FILE = os.path.join(DATA_DIR, 'balance_add_log.json')
BALANCE_DEDUCT_LOG_FILE = os.path.join(DATA_DIR, 'balance_deduct_log.json')

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Default product prices
DEFAULT_PRICES = {
    "Çay": 1,
    "Büyük Çay": 2,
    "Kahve (sade)": 4,
    "Kahve (orta)": 4,
    "Kahve (şekerli)": 4,
    "Duble Kahve (sade)": 8,
    "Duble Kahve (orta)": 8,
    "Duble Kahve (şekerli)": 8,
    "Duble Az Telveli Kahve (sade)": 5,
    "Duble Az Telveli Kahve (orta)": 5,
    "Duble Az Telveli Kahve (şekerli)": 5,
    "Madensuyu": 5,
    "Meyveli Madensuyu": 6,
    "Sıcak Su": 1,
    "Su": 1,
    "Ihlamur": 1,
    "Büyük Ihlamur": 2,
    "Oralet (portakal)": 1,
    "Oralet (kuşburnu)": 1,
    "Oralet (elma)": 1,
    "Oralet (kiwi)": 1,
    "Oralet (karadut)": 1,
    "Oralet (atom)": 1,
    "Kış Çayı": 1
}

# Active orders
active_orders = []
# Connected clients
clients = {}
# Order queue for batch saving
order_queue = deque(maxlen=50)

# Helper function for password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize data files
def init_data_files():
    # Initialize prices file
    if not os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_PRICES, f, ensure_ascii=False, indent=4)
    
    # Initialize stock file with all products active
    if not os.path.exists(STOCK_FILE):
        stock_status = {product: True for product in DEFAULT_PRICES.keys()}
        with open(STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(stock_status, f, ensure_ascii=False, indent=4)
    
    # Initialize computers file
    if not os.path.exists(COMPUTERS_FILE):
        with open(COMPUTERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    
    # Initialize notes file
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"server_note": ""}, f, ensure_ascii=False, indent=4)
    
    # Initialize frequent orders file
    if not os.path.exists(FREQUENT_ORDERS_FILE):
        with open(FREQUENT_ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    
    # Initialize users file
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
            
    # Initialize passwords file
    if not os.path.exists(PASSWORDS_FILE):
        with open(PASSWORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
            
    # Initialize rooms file
    if not os.path.exists(ROOMS_FILE):
        with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    
    # Initialize active orders file
    if not os.path.exists(ACTIVE_ORDERS_FILE):
        with open(ACTIVE_ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            
    # Initialize log files
    if not os.path.exists(ORDER_LOG_FILE):
        with open(ORDER_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            
    if not os.path.exists(BALANCE_TRANSFER_LOG_FILE):
        with open(BALANCE_TRANSFER_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            
    if not os.path.exists(BALANCE_ADD_LOG_FILE):
        with open(BALANCE_ADD_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            
    if not os.path.exists(BALANCE_DEDUCT_LOG_FILE):
        with open(BALANCE_DEDUCT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            
    # Run migration to convert computers to rooms
    migrate_computers_to_rooms()
    
    # Make sure all existing users have password entries
    sync_passwords_with_users()
    
    # Load active orders into global variable
    global active_orders
    active_orders = load_active_orders()

def sync_passwords_with_users():
    """Make sure all users have a password entry"""
    users = load_users()
    passwords = load_passwords()
    
    modified = False
    for user_id in users:
        if user_id not in passwords:
            passwords[user_id] = "123"  # Default password
            modified = True
    
    if modified:
        save_passwords(passwords)
        print("Passwords synced with users")

# Migrate computers to rooms
def migrate_computers_to_rooms():
    if os.path.exists(COMPUTERS_FILE) and not os.path.exists(ROOMS_FILE):
        try:
            with open(COMPUTERS_FILE, 'r', encoding='utf-8') as file:
                computers = json.load(file)
            
            # Convert each computer to a room with 4 persons
            rooms = {}
            for computer in computers:
                rooms[computer] = ["kişi1", "kişi2", "kişi3", "kişi4"]
            
            # Save to rooms.json
            with open(ROOMS_FILE, 'w', encoding='utf-8') as file:
                json.dump(rooms, file, ensure_ascii=False, indent=4)
            
            # Initialize users with default passwords and 100 TL balance
            users = load_users()
            passwords = load_passwords()
            for room in rooms:
                for person in rooms[room]:
                    user_id = f"{room}:{person}"
                    if user_id not in users:
                        users[user_id] = {
                            "first_login": True,
                            "room": room,
                            "person": person,
                            "balance": 100
                        }
                        passwords[user_id] = "123"  # Set default password
            
            # Save users and passwords
            save_users(users)
            save_passwords(passwords)
                
            print("Migration from computers to rooms completed successfully")
            
        except Exception as e:
            print(f"Error during migration: {e}")

# Helper functions
def load_prices():
    try:
        with open(PRICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return DEFAULT_PRICES

def load_stock():
    try:
        with open(STOCK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Default all products to available
        stock_status = {product: True for product in DEFAULT_PRICES.keys()}
        return stock_status

def load_computers():
    try:
        with open(COMPUTERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def load_notes():
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"server_note": ""}

def load_frequent_orders():
    try:
        with open(FREQUENT_ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def load_rooms():
    try:
        with open(ROOMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_rooms(rooms):
    with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(rooms, f, ensure_ascii=False, indent=4)

def load_order_history():
    try:
        if os.path.exists(ORDER_LOG_FILE):
            with open(ORDER_LOG_FILE, 'r', encoding='utf-8') as f:
                order_logs = json.load(f)
            return order_logs
    except Exception as e:
        print(f"Sipariş geçmişi yükleme hatası: {e}")
    return []

def get_user_orders(room, person):
    all_orders = load_order_history()
    return [order for order in all_orders if order['room'] == room and order['person'] == person]

# Authentication check decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Add admin check decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            # Check if this is an API request or a page request
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "Admin yetkisi gerekli"}), 403
            else:
                # Redirect to admin login for page requests
                return redirect(url_for('admin'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        room = request.form.get('room')
        person = request.form.get('person')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        rooms = load_rooms()
        users = load_users()
        passwords = load_passwords()
        
        user_id = f"{room}:{person}"
        
        # Check if room exists
        if room not in rooms:
            flash('Oda bulunamadı.')
            return render_template('login.html', rooms=rooms)
        
        # Check if user exists in room
        if user_id not in users:
            # If user doesn't exist, create with default password and 100 TL balance
            users[user_id] = {
                "first_login": True,
                "room": room,
                "person": person,
                "balance": 100
            }
            passwords[user_id] = "123"  # Default password
            save_users(users)
            save_passwords(passwords)
        elif "balance" not in users[user_id]:
            # If existing user doesn't have balance, add it
            users[user_id]["balance"] = 100
            save_users(users)
        
        # Check password
        if passwords.get(user_id) == password:
            session.permanent = remember
            session['user_id'] = user_id
            session['room'] = room
            session['person'] = person
            
            # Check if it's user's first login
            if users[user_id].get("first_login", False):
                flash('İlk giriş yapıyorsunuz. Lütfen şifrenizi değiştirin.', 'info')
                return redirect(url_for('change_password'))
                
            return redirect(url_for('index'))
        else:
            flash('Hatalı şifre.')
    
    return render_template('login.html', rooms=load_rooms())

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('room', None)
    session.pop('person', None)
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user_id = session.get('user_id')
    users = load_users()
    first_login = False
    
    # Check if this is the user's first login
    if user_id in users and users[user_id].get("first_login", False):
        first_login = True
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        passwords = load_passwords()
        
        # Check old password
        if passwords.get(user_id) != old_password:
            flash('Eski şifre hatalı.')
            return render_template('change_password.html', first_login=first_login)
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash('Yeni şifreler eşleşmiyor.')
            return render_template('change_password.html', first_login=first_login)
        
        # Update password
        passwords[user_id] = new_password
        users[user_id]["first_login"] = False
        save_users(users)
        save_passwords(passwords)
        
        flash('Şifreniz başarıyla değiştirildi.', 'success')
        
        # If this was first login, redirect to index
        if first_login:
            return redirect(url_for('index'))
        else:
            return redirect(url_for('index'))
    
    return render_template('change_password.html', first_login=first_login)

@app.route('/balance_transfer', methods=['GET', 'POST'])
@login_required
def balance_transfer():
    rooms = load_rooms()
    
    if request.method == 'POST':
        to_room = request.form.get('room')
        to_person = request.form.get('person')
        amount = request.form.get('amount')
        
        try:
            amount = float(amount)
        except ValueError:
            flash('Geçersiz miktar.')
            return render_template('balance_transfer.html', rooms=rooms)
        
        if amount <= 0:
            flash('Miktar sıfırdan büyük olmalıdır.')
            return render_template('balance_transfer.html', rooms=rooms)
        
        from_user_id = session.get('user_id')
        to_user_id = f"{to_room}:{to_person}"
        
        success, message = transfer_balance(from_user_id, to_user_id, amount)
        if success:
            # Bakiye transferini logla
            log_balance_transfer(from_user_id, to_user_id, amount)
            flash(f'Transfer başarılı. {amount} TL gönderildi.', 'success')
        else:
            flash(message)
    
    return render_template('balance_transfer.html', rooms=rooms)

@app.route('/index')
@login_required
def index():
    return render_template('index.html', room=session.get('room'), person=session.get('person'))

@app.route('/admin')
def admin():
    if session.get('is_admin', False):
        return render_template('admin.html')
    else:
        return redirect(url_for('admin_login'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':  # Simple admin authentication
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('Hatalı admin şifresi')
    
    return render_template('admin_login.html')

@app.route('/user_orders')
@login_required
def user_orders():
    # Since we removed Excel-based order history, we'll use active orders and order logs
    return render_template('user_orders.html', orders=[])

@app.route('/balance_management')
@admin_required
def balance_management():
    return render_template('balance_management.html')

# API Endpoints
@app.route('/api/prices', methods=['GET'])
def get_prices():
    return jsonify(load_prices())

@app.route('/api/prices', methods=['POST'])
def update_prices():
    if request.is_json:
        prices = request.get_json()
        with open(PRICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(prices, f, ensure_ascii=False, indent=4)
        socketio.emit('prices_updated', prices)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid data format"}), 400

@app.route('/api/stock', methods=['GET'])
def get_stock():
    return jsonify(load_stock())

@app.route('/api/stock', methods=['POST'])
def update_stock():
    if request.is_json:
        stock = request.get_json()
        with open(STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(stock, f, ensure_ascii=False, indent=4)
        socketio.emit('stock_updated', stock)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid data format"}), 400

@app.route('/api/computers', methods=['GET'])
def get_computers():
    # For backwards compatibility, convert rooms to computers list
    rooms = load_rooms()
    computers = list(rooms.keys())
    return jsonify(computers)

@app.route('/api/computers', methods=['POST'])
def update_computers():
    # This method is kept for backward compatibility
    data = request.json
    computers = data.get('computers', [])
    
    # Update rooms instead of computers
    rooms = load_rooms()
    
    # For each new computer not in rooms, add it as a room
    for computer in computers:
        if computer not in rooms:
            rooms[computer] = ["kişi1", "kişi2", "kişi3", "kişi4"]
    
    # Save rooms
    save_rooms(rooms)
    
    # Update users for new rooms
    users = load_users()
    passwords = load_passwords()
    for room in rooms:
        for person in rooms[room]:
            user_key = f"{room}:{person}"
            if user_key not in users:
                users[user_key] = {
                    "first_login": True,
                    "room": room,
                    "person": person,
                    "balance": 100
                }
                passwords[user_key] = "123"  # Set default password
    
    save_users(users)
    save_passwords(passwords)
    
    return jsonify({"status": "success"})

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    return jsonify(load_rooms())

@app.route('/api/rooms', methods=['POST'])
def update_rooms():
    data = request.json
    rooms = data.get('rooms', {})
    
    # Load current users
    users = load_users()
    passwords = load_passwords()
    
    # Add new users for new rooms or new persons
    for room, persons in rooms.items():
        for person in persons:
            user_id = f"{room}:{person}"
            if user_id not in users:
                users[user_id] = {
                    "first_login": True,
                    "room": room,
                    "person": person,
                    "balance": 100  # Initialize with 100 TL
                }
                passwords[user_id] = "123"  # Default password
    
    # Remove users for removed rooms or persons
    current_rooms = load_rooms()
    to_remove = []
    
    for user_id in users:
        if ":" in user_id:
            room, person = user_id.split(":", 1)
            if room not in rooms or (room in rooms and person not in rooms[room]):
                to_remove.append(user_id)
    
    for user_id in to_remove:
        users.pop(user_id, None)
        passwords.pop(user_id, None)  # Also remove from passwords
    
    # Save rooms, users and passwords
    save_rooms(rooms)
    save_users(users)
    save_passwords(passwords)
    
    return jsonify({"status": "success"})

@app.route('/api/room/<room_name>/persons', methods=['GET'])
def get_room_persons(room_name):
    rooms = load_rooms()
    if room_name in rooms:
        return jsonify(rooms[room_name])
    return jsonify([])

@app.route('/api/note', methods=['GET'])
def get_note():
    notes = load_notes()
    return jsonify({"server_note": notes.get("server_note", "")})

@app.route('/api/note', methods=['POST'])
def update_note():
    if request.is_json:
        data = request.get_json()
        note = data.get("server_note", "")
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"server_note": note}, f, ensure_ascii=False, indent=4)
        socketio.emit('note_updated', {"server_note": note})
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid data format"}), 400

@app.route('/api/frequent-orders', methods=['GET'])
def get_frequent_orders():
    if 'user_id' in session:
        user_id = session['user_id']
        all_orders = load_frequent_orders()
        if user_id in all_orders:
            return jsonify(all_orders[user_id])
    return jsonify({})

@app.route('/api/frequent-order', methods=['POST'])
def add_frequent_order():
    if request.is_json and 'user_id' in session:
        data = request.get_json()
        name = data.get('name')
        order = data.get('order')
        
        if not all([name, order]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        # Load existing orders
        frequent_orders = load_frequent_orders()
        user_id = session['user_id']
        
        # Initialize user's orders if not exist
        if user_id not in frequent_orders:
            frequent_orders[user_id] = {}
            
        # Add new order
        frequent_orders[user_id][name] = order
        
        # Save to file
        with open(FREQUENT_ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(frequent_orders, f, ensure_ascii=False, indent=4)
        
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid data format"}), 400

@app.route('/api/order-history', methods=['GET'])
def get_order_history():
    # Since we no longer have Excel-based order history, return order logs instead
    try:
        with open(ORDER_LOG_FILE, 'r', encoding='utf-8') as f:
            order_logs = json.load(f)
        return jsonify(order_logs)
    except:
        return jsonify([])

@app.route('/api/user-orders', methods=['GET'])
@login_required
def api_user_orders():
    room = session.get('room')
    person = session.get('person')
    
    # Since we removed Excel-based user orders, return filtered order logs
    try:
        with open(ORDER_LOG_FILE, 'r', encoding='utf-8') as f:
            all_orders = json.load(f)
        
        user_orders = [order for order in all_orders 
                       if order.get('room') == room and order.get('person') == person]
        return jsonify(user_orders)
    except:
        return jsonify([])

@app.route('/api/balance', methods=['GET'])
@login_required
def get_balance():
    user_id = session.get('user_id')
    balance = get_user_balance(user_id)
    return jsonify({"balance": balance})

@app.route('/api/balance/add', methods=['POST'])
@admin_required
def add_balance():
    data = request.get_json()
    user_id = data.get('user_id')  # Now we need user_id since admin adds balance
    amount = data.get('amount')
    
    if not all([user_id, amount]) or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"status": "error", "message": "Geçersiz miktar veya kullanıcı"}), 400
    
    admin_id = session.get('user_id')
    
    if update_user_balance(user_id, amount):
        # Bakiye ekleme işlemini logla
        log_balance_add(admin_id, user_id, amount)
        
        new_balance = get_user_balance(user_id)
        return jsonify({"status": "success", "balance": new_balance})
    
    return jsonify({"status": "error", "message": "Bakiye güncellenemedi"}), 400

@app.route('/api/users/balances', methods=['GET'])
@admin_required
def get_all_balances():
    users = load_users()
    balances = {user_id: user_data.get('balance', 0) for user_id, user_data in users.items()}
    return jsonify(balances)

@app.route('/api/balance/transfer', methods=['POST'])
@login_required
def transfer_balance_endpoint():
    data = request.get_json()
    to_room = data.get('room')
    to_person = data.get('person')
    amount = data.get('amount')
    
    if not all([to_room, to_person, amount]) or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"status": "error", "message": "Geçersiz transfer bilgileri"}), 400
    
    from_user_id = session.get('user_id')
    to_user_id = f"{to_room}:{to_person}"
    
    success, message = transfer_balance(from_user_id, to_user_id, amount)
    if success:
        # Bakiye transferini logla
        log_balance_transfer(from_user_id, to_user_id, amount)
        
        new_balance = get_user_balance(from_user_id)
        return jsonify({
            "status": "success",
            "message": message,
            "balance": new_balance
        })
    
    return jsonify({"status": "error", "message": message}), 400

@app.route('/api/order', methods=['POST'])
@login_required
def place_order():
    try:
        data = request.get_json()
        order = data.get('order')
        note = data.get('note', '')
        total_price = data.get('total_price', 0)
        
        print(f"Gelen sipariş verileri: order={order}, note={note}, total_price={total_price}")
        
        # Ensure total_price is a float
        if isinstance(total_price, str):
            # Remove currency symbols and format properly
            clean_price = total_price.replace('₺', '').replace(',', '.').strip()
            try:
                total_price = float(clean_price)
                print(f"String fiyat dönüştürüldü: {clean_price} -> {total_price}")
            except ValueError:
                print(f"Fiyat dönüştürülemedi: {clean_price}")
                return jsonify({"status": "error", "message": "Geçersiz fiyat formatı"}), 400
        else:
            # Ensure numeric type
            total_price = float(total_price)
            print(f"Sayısal fiyat: {total_price}")
            
        # Validate order and price
        if not order or not order.strip():
            print("Sipariş boş")
            return jsonify({"status": "error", "message": "Sipariş içeriği boş"}), 400
            
        if total_price <= 0:
            print(f"Geçersiz fiyat: {total_price}")
            return jsonify({"status": "error", "message": f"Geçersiz fiyat: {total_price}"}), 400
        
        # Get user info from session
        room = session.get('room')
        person = session.get('person')
        user_id = session.get('user_id')
        
        print(f"Kullanıcı bilgileri: user_id={user_id}, room={room}, person={person}")
        
        # Check user balance
        user_balance = get_user_balance(user_id)
        print(f"Kullanıcı bakiyesi: {user_balance}, Sipariş tutarı: {total_price}")
        
        if user_balance < total_price:
            print("Yetersiz bakiye")
            return jsonify({
                "status": "error",
                "message": f"Yetersiz bakiye. Mevcut bakiye: {user_balance:.2f} ₺, Gerekli tutar: {total_price:.2f} ₺"
            }), 400
        
        # Check if items are in stock
        stock = load_stock()
        order_items = []
        for line in order.split('\n'):
            if line.strip():
                parts = line.split(' x ')
                if len(parts) >= 2:
                    order_items.append(parts[1].strip())
                    
        print(f"Sipariş kalemleri: {order_items}")
        
        out_of_stock = [item for item in order_items if item in stock and not stock[item]]
        
        if out_of_stock:
            print(f"Stokta olmayan ürünler: {out_of_stock}")
            return jsonify({
                "status": "error", 
                "message": f"Stokta olmayan ürünler: {', '.join(out_of_stock)}", 
                "out_of_stock": out_of_stock
            }), 400
        
        # Deduct balance
        update_user_balance(user_id, -total_price)
        
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create order object
        order_obj = {
            "order_id": int(time.time() * 1000),  # Unique ID based on timestamp
            "order_time": order_time,
            "room": room,
            "person": person,
            "order": order,
            "note": note,
            "total_price": total_price,
            "status": "Beklemede",
            "start_time": time.time()
        }
        
        # Add to active orders
        active_orders.append(order_obj)
        
        # Aktif siparişleri kaydet
        save_active_orders(active_orders)
        
        # Sipariş logunu kaydet
        log_order(user_id, room, person, order_obj)
        
        # Notify admin
        socketio.emit('new_order', order_obj)
        
        # Get updated balance
        new_balance = get_user_balance(user_id)
        
        print(f"Sipariş başarıyla oluşturuldu: order_id={order_obj['order_id']}, new_balance={new_balance}")
        
        return jsonify({
            "status": "success", 
            "order_id": order_obj["order_id"],
            "balance": new_balance
        })
        
    except Exception as e:
        print(f"Sipariş oluşturma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Beklenmeyen hata: {str(e)}"}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(active_orders)

@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({"status": "error", "message": "Status not provided"}), 400
    
    global active_orders
    
    # First find the order
    order_to_update = None
    for order in active_orders:
        if order['order_id'] == order_id:
            order_to_update = order
            break
    
    if order_to_update:
        old_status = order_to_update['status']  # Önceki durum
        order_to_update['status'] = new_status
        
        # Make a copy of the updated order before removing it from active_orders
        updated_order = order_to_update.copy()
        
        # If completed, add delivery time and remove from active orders
        if new_status == "Tamamlandı":
            delivery_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_order['delivery_time'] = delivery_time
            # Remove from active orders (after processing)
            active_orders = [order for order in active_orders if order['order_id'] != order_id]
            
        # If canceled, add reason and refund the balance
        elif new_status == "İptal Edildi":
            reason = data.get('reason', 'Belirtilmedi')
            updated_order['cancel_reason'] = reason
            
            # Bakiyeyi iade et (sadece Beklemede durumundayken iptal edildiyse)
            if old_status == "Beklemede" and 'total_price' in updated_order:
                user_id = f"{updated_order['room']}:{updated_order['person']}"
                # Kullanıcıya bakiyesini geri yükle
                update_user_balance(user_id, updated_order['total_price'])
            
            # Remove from active orders (after processing)
            active_orders = [order for order in active_orders if order['order_id'] != order_id]
        
        # Aktif siparişleri kaydet
        save_active_orders(active_orders)
        
        # Notify clients about status change
        notification_data = {
            'order_id': order_id,
            'status': new_status,
            'room': updated_order['room'],
            'person': updated_order['person'],
            'reason': data.get('reason', '') if new_status == "İptal Edildi" else None
        }
        
        # İade edildiyse yeni bakiyeyi de bildir
        if new_status == "İptal Edildi" and old_status == "Beklemede" and 'total_price' in updated_order:
            user_id = f"{updated_order['room']}:{updated_order['person']}"
            notification_data['new_balance'] = get_user_balance(user_id)
            
        socketio.emit('order_status_updated', notification_data)
        
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Order not found"}), 404

# SocketIO events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    clients[request.sid] = {"type": "unknown"}

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in clients:
        del clients[request.sid]

@socketio.on('register_client')
def handle_register_client(data):
    client_type = data.get('type')
    room = data.get('room')
    person = data.get('person')
    
    if client_type and request.sid in clients:
        clients[request.sid]["type"] = client_type
        if room:
            clients[request.sid]["room"] = room
        if person:
            clients[request.sid]["person"] = person
        
        # Send current prices and stock to clients
        if client_type == "customer":
            emit('prices_updated', load_prices())
            emit('stock_updated', load_stock())
            emit('note_updated', {"server_note": load_notes().get("server_note", "")})
        elif client_type == "admin":
            # Reload active orders from file to ensure we have the latest data
            global active_orders
            active_orders = load_active_orders()
            # Send active orders to admin
            emit('active_orders', active_orders)

@socketio.on('get_active_orders')
def handle_get_active_orders():
    # Reload active orders from file to ensure we have the latest data
    global active_orders
    active_orders = load_active_orders()
    emit('active_orders', active_orders)

# Balance management functions
def get_user_balance(user_id):
    users = load_users()
    if user_id in users:
        return users[user_id].get("balance", 0)
    return 0

def update_user_balance(user_id, amount):
    users = load_users()
    if user_id in users:
        users[user_id]["balance"] = users[user_id].get("balance", 0) + amount
        save_users(users)
        return True
    return False

def transfer_balance(from_user_id, to_user_id, amount):
    users = load_users()
    if from_user_id not in users or to_user_id not in users:
        return False, "Kullanıcı bulunamadı"
    
    from_balance = users[from_user_id].get("balance", 0)
    if from_balance < amount:
        return False, "Yetersiz bakiye"
    
    # Update balances
    users[from_user_id]["balance"] = from_balance - amount
    users[to_user_id]["balance"] = users[to_user_id].get("balance", 0) + amount
    save_users(users)
    return True, "Transfer başarılı"

def load_passwords():
    try:
        with open(PASSWORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_passwords(passwords):
    with open(PASSWORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(passwords, f, ensure_ascii=False, indent=4)

# Aktif siparişleri yükleme fonksiyonu
def load_active_orders():
    try:
        with open(ACTIVE_ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# Aktif siparişleri kaydetme fonksiyonu
def save_active_orders(orders):
    with open(ACTIVE_ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

# Sipariş logunu ekleme
def log_order(user_id, room, person, order_data):
    try:
        # Log kaydı oluştur
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "room": room,
            "person": person,
            "order_id": order_data["order_id"],
            "order": order_data["order"],
            "total_price": order_data["total_price"],
            "note": order_data.get("note", "")
        }
        
        # Mevcut logları yükle
        logs = []
        try:
            with open(ORDER_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
        
        # Yeni logu ekle
        logs.append(log_entry)
        
        # Dosyaya kaydet
        with open(ORDER_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Sipariş log hatası: {e}")
        return False

# Bakiye transferi log kaydı
def log_balance_transfer(from_user_id, to_user_id, amount):
    try:
        # Log kaydı oluştur
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "amount": amount
        }
        
        # Mevcut logları yükle
        logs = []
        try:
            with open(BALANCE_TRANSFER_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
        
        # Yeni logu ekle
        logs.append(log_entry)
        
        # Dosyaya kaydet
        with open(BALANCE_TRANSFER_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Bakiye transfer log hatası: {e}")
        return False

# Admin bakiye ekleme log kaydı
def log_balance_add(admin_id, user_id, amount):
    try:
        # Log kaydı oluştur
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "admin_id": admin_id,
            "user_id": user_id,
            "amount": amount
        }
        
        # Mevcut logları yükle
        logs = []
        try:
            with open(BALANCE_ADD_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
        
        # Yeni logu ekle
        logs.append(log_entry)
        
        # Dosyaya kaydet
        with open(BALANCE_ADD_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Bakiye ekleme log hatası: {e}")
        return False

# Log kayıtlarını görüntüleme API'leri
@app.route('/api/logs/orders', methods=['GET'])
@admin_required
def get_order_logs():
    try:
        with open(ORDER_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return jsonify(logs)
    except:
        return jsonify([])

@app.route('/api/logs/balance-transfers', methods=['GET'])
@admin_required
def get_balance_transfer_logs():
    try:
        with open(BALANCE_TRANSFER_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return jsonify(logs)
    except:
        return jsonify([])

@app.route('/api/logs/balance-additions', methods=['GET'])
@admin_required
def get_balance_add_logs():
    try:
        with open(BALANCE_ADD_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return jsonify(logs)
    except:
        return jsonify([])

@app.route('/api/balance/deduct', methods=['POST'])
@admin_required
def deduct_balance():
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    
    if not all([user_id, amount]) or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"status": "error", "message": "Geçersiz miktar veya kullanıcı"}), 400
    
    admin_id = session.get('user_id')
    
    # Check current balance to prevent negative balance
    current_balance = get_user_balance(user_id)
    
    # If requested deduction is more than current balance, only deduct what's available
    if amount > current_balance:
        # Adjust the amount to the current balance (make it zero but not negative)
        amount = current_balance
        if amount == 0:
            return jsonify({"status": "error", "message": "Kullanıcının bakiyesi zaten 0"}), 400
    
    # Make amount negative for deduction
    deduction_amount = -amount
    
    if update_user_balance(user_id, deduction_amount):
        # Log balance deduction
        log_balance_deduct(admin_id, user_id, amount)
        
        new_balance = get_user_balance(user_id)
        return jsonify({"status": "success", "balance": new_balance, "deducted_amount": amount})
    
    return jsonify({"status": "error", "message": "Bakiye güncellenemedi"}), 400

# Admin bakiyeden düşme log kaydı
def log_balance_deduct(admin_id, user_id, amount):
    try:
        # Log kaydı oluştur
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "admin_id": admin_id,
            "user_id": user_id,
            "amount": amount
        }
        
        # Mevcut logları yükle
        logs = []
        try:
            with open(BALANCE_DEDUCT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
        
        # Yeni logu ekle
        logs.append(log_entry)
        
        # Dosyaya kaydet
        with open(BALANCE_DEDUCT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Bakiye düşme log hatası: {e}")
        return False

@app.route('/api/logs/balance-deductions', methods=['GET'])
@admin_required
def get_balance_deduct_logs():
    try:
        with open(BALANCE_DEDUCT_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return jsonify(logs)
    except:
        return jsonify([])

# Initialize and run the application
if __name__ == '__main__':
    init_data_files()
    # Render uses PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    # Use threading mode for compatibility with Python 3.11
    socketio.run(app, debug=False, host='0.0.0.0', port=port) 