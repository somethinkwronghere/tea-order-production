import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# Application Configuration
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'tea-order-secret-key'

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
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

# Ensure static and templates directories exist
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

# Routes
@app.route('/')
def index():
    """Main page - shows ordering interface"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin page for viewing and managing orders"""
        return render_template('admin.html')

# API Endpoints
@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Get menu prices"""
    return jsonify(DEFAULT_PRICES)

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all active orders"""
    return jsonify(active_orders)

@app.route('/api/order', methods=['POST'])
def place_order():
    """Place a new order"""
    data = request.json
    order_text = data.get('order')
    
    if not order_text:
        return jsonify({"error": "Sipariş içeriği boş olamaz"}), 400
    
    order = {
        'id': len(active_orders) + 1,
        'order': order_text,
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'Hazırlanıyor'
    }
    
    active_orders.append(order)
    return jsonify({"success": True, "order_id": order['id']})

@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """Update order status (admin only)"""
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({"error": "Durum belirtilmedi"}), 400
    
    for order in active_orders:
        if order['id'] == order_id:
            order['status'] = new_status
            
            # If order is completed or canceled, remove from active orders
            if new_status in ['Tamamlandı', 'İptal Edildi']:
                active_orders.remove(order)
                
            return jsonify({"success": True})
    
    return jsonify({"error": "Sipariş bulunamadı"}), 404

# Create template files
def create_index_html():
    """Create the index.html template if it doesn't exist"""
    index_html = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Çay Sipariş Sistemi</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .menu-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        .menu-item:hover {
            background-color: #f9f9f9;
        }
        button {
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background-color: #45a049;
        }
        #order-summary {
            margin-top: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
        #status-message {
            margin-top: 20px;
            padding: 10px;
            background-color: #e8f5e9;
            border-left: 5px solid #4CAF50;
            display: none;
        }
        #error-message {
            margin-top: 20px;
            padding: 10px;
            background-color: #ffebee;
            border-left: 5px solid #f44336;
            display: none;
        }
        #active-orders {
            margin-top: 20px;
        }
        .order-item {
            padding: 10px;
            border: 1px solid #ddd;
            margin-bottom: 10px;
            background-color: #fff;
        }
    </style>
</head>
<body>
    <h1>Çay Sipariş Sistemi</h1>
    
    <div>
        <h2>Menü</h2>
        <div id="menu-items"></div>
    </div>
    
    <div id="order-form">
        <h2>Sipariş Ver</h2>
        <div id="order-items"></div>
        <div id="order-summary">
            <h3>Sipariş Özeti</h3>
            <div id="order-summary-items"></div>
            <p>Toplam: <span id="total-price">0</span> TL</p>
        </div>
        <button id="place-order-btn">Sipariş Ver</button>
        <button id="clear-order-btn">Temizle</button>
    </div>
    
    <div id="status-message"></div>
    <div id="error-message"></div>
    
    <div id="active-orders">
        <h2>Aktif Siparişlerim</h2>
        <div id="order-items-container"></div>
    </div>
    
    <p><a href="/admin">Admin Paneli</a></p>
    
    <script>
        // Sipariş verileri
        let orderItems = {};
        let prices = {};
        
        // Sayfa yüklendiğinde çalışacak kod
        document.addEventListener('DOMContentLoaded', function() {
            fetchPrices();
            fetchOrders();
            
            // Sipariş verme butonu
            document.getElementById('place-order-btn').addEventListener('click', placeOrder);
            
            // Temizle butonu
            document.getElementById('clear-order-btn').addEventListener('click', clearOrder);
            
            // Her 10 saniyede bir siparişleri yenile
            setInterval(fetchOrders, 10000);
        });
        
        // Fiyatları getir
        function fetchPrices() {
            fetch('/api/prices')
                .then(response => response.json())
                .then(data => {
                    prices = data;
                    displayMenu(data);
                })
                .catch(error => {
                    console.error('Fiyatlar alınamadı:', error);
                    showError('Fiyatlar yüklenirken bir hata oluştu.');
                });
        }
        
        // Siparişleri getir
        function fetchOrders() {
            fetch('/api/orders')
                .then(response => response.json())
                .then(data => {
                    displayOrders(data);
                })
                .catch(error => {
                    console.error('Siparişler alınamadı:', error);
                });
        }
        
        // Menüyü göster
        function displayMenu(prices) {
            const menuDiv = document.getElementById('menu-items');
            menuDiv.innerHTML = '';
            
            for (const [item, price] of Object.entries(prices)) {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'menu-item';
                
                itemDiv.innerHTML = `
                    <span>${item} - ${price} TL</span>
                    <button onclick="addToOrder('${item}')">Ekle</button>
                `;
                
                menuDiv.appendChild(itemDiv);
            }
        }
        
        // Siparişleri göster
        function displayOrders(orders) {
            const ordersDiv = document.getElementById('order-items-container');
            ordersDiv.innerHTML = '';
            
            if (orders.length === 0) {
                ordersDiv.innerHTML = '<p>Aktif sipariş bulunmuyor.</p>';
                return;
            }
            
            for (const order of orders) {
                const orderDiv = document.createElement('div');
                orderDiv.className = 'order-item';
                
                orderDiv.innerHTML = `
                    <h3>Sipariş #${order.id}</h3>
                    <p><strong>Sipariş:</strong> ${order.order}</p>
                    <p><strong>Zaman:</strong> ${order.time}</p>
                    <p><strong>Durum:</strong> ${order.status}</p>
                `;
                
                ordersDiv.appendChild(orderDiv);
            }
        }
        
        // Siparişe ürün ekle
        function addToOrder(item) {
            if (orderItems[item]) {
                orderItems[item]++;
            } else {
                orderItems[item] = 1;
            }
            
            updateOrderSummary();
        }
        
        // Sipariş özetini güncelle
        function updateOrderSummary() {
            const summaryDiv = document.getElementById('order-summary-items');
            summaryDiv.innerHTML = '';
            
            let total = 0;
            
            for (const [item, quantity] of Object.entries(orderItems)) {
                if (quantity > 0) {
                    const itemPrice = prices[item] * quantity;
                    total += itemPrice;
                    
                    const itemDiv = document.createElement('div');
                    itemDiv.innerHTML = `
                        <p>${item} x ${quantity} = ${itemPrice} TL 
                        <button onclick="removeFromOrder('${item}')">-</button>
                        <button onclick="addToOrder('${item}')">+</button>
                        </p>
                    `;
                    
                    summaryDiv.appendChild(itemDiv);
                }
            }
            
            document.getElementById('total-price').textContent = total;
        }
        
        // Siparişten ürün çıkar
        function removeFromOrder(item) {
            if (orderItems[item] && orderItems[item] > 0) {
                orderItems[item]--;
                if (orderItems[item] === 0) {
                    delete orderItems[item];
                }
                updateOrderSummary();
            }
        }
        
        // Siparişi temizle
        function clearOrder() {
            orderItems = {};
            updateOrderSummary();
        }
        
        // Sipariş ver
        function placeOrder() {
            const orderText = Object.entries(orderItems)
                .filter(([_, quantity]) => quantity > 0)
                .map(([item, quantity]) => `${quantity} x ${item}`)
                .join(", ");
                
            if (!orderText) {
                showError('Lütfen sipariş vermek için ürün ekleyin.');
                return;
            }
            
            fetch('/api/order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order: orderText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess(`Siparişiniz alındı! Sipariş numarası: ${data.order_id}`);
                    clearOrder();
                    fetchOrders();
                } else {
                    showError(data.error || 'Sipariş verirken bir hata oluştu.');
                }
            })
            .catch(error => {
                console.error('Sipariş verme hatası:', error);
                showError('Sipariş verirken bir hata oluştu.');
            });
        }
        
        // Başarı mesajı göster
        function showSuccess(message) {
            const statusDiv = document.getElementById('status-message');
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
            
            // Hata mesajını gizle
            document.getElementById('error-message').style.display = 'none';
            
            // 5 saniye sonra mesajı gizle
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
        
        // Hata mesajı göster
        function showError(message) {
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            
            // Başarı mesajını gizle
            document.getElementById('status-message').style.display = 'none';
            
            // 5 saniye sonra mesajı gizle
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>'''
    
    file_path = os.path.join(TEMPLATES_DIR, 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(index_html)

def create_admin_html():
    """Create the admin.html template if it doesn't exist"""
    admin_html = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Çay Sipariş Sistemi</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .order-item {
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .order-actions {
            margin-top: 10px;
        }
        button {
            padding: 8px 16px;
            margin-right: 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .complete-btn {
            background-color: #4CAF50;
            color: white;
        }
        .cancel-btn {
            background-color: #f44336;
            color: white;
        }
        .refresh-btn {
            background-color: #2196F3;
            color: white;
            margin-bottom: 20px;
        }
        #status-message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: none;
        }
        .success {
            background-color: #e8f5e9;
            border-left: 5px solid #4CAF50;
        }
        .error {
            background-color: #ffebee;
            border-left: 5px solid #f44336;
        }
    </style>
</head>
<body>
    <h1>Admin Panel - Çay Sipariş Sistemi</h1>
    
    <button id="refresh-orders" class="refresh-btn">Siparişleri Yenile</button>
    
    <div id="status-message"></div>
    
    <div id="active-orders">
        <h2>Aktif Siparişler</h2>
        <div id="orders-container"></div>
    </div>
    
    <p><a href="/">Ana Sayfa</a></p>
    
    <script>
        // Sayfa yüklendiğinde çalışacak kod
        document.addEventListener('DOMContentLoaded', function() {
            fetchOrders();
            
            // Yenile butonu
            document.getElementById('refresh-orders').addEventListener('click', fetchOrders);
            
            // Her 5 saniyede bir otomatik yenile
            setInterval(fetchOrders, 5000);
        });
        
        // Siparişleri getir
        function fetchOrders() {
            fetch('/api/orders')
                .then(response => response.json())
                .then(data => {
                    displayOrders(data);
                })
                .catch(error => {
                    console.error('Siparişler alınamadı:', error);
                    showMessage('Siparişler alınırken bir hata oluştu.', 'error');
                });
        }
        
        // Siparişleri göster
        function displayOrders(orders) {
            const container = document.getElementById('orders-container');
            container.innerHTML = '';
            
            if (orders.length === 0) {
                container.innerHTML = '<p>Aktif sipariş bulunmuyor.</p>';
                return;
            }
            
            for (const order of orders) {
                const orderDiv = document.createElement('div');
                orderDiv.className = 'order-item';
                orderDiv.innerHTML = `
                    <h3>Sipariş #${order.id}</h3>
                    <p><strong>Sipariş:</strong> ${order.order}</p>
                    <p><strong>Zaman:</strong> ${order.time}</p>
                    <p><strong>Durum:</strong> ${order.status || 'Hazırlanıyor'}</p>
                    <div class="order-actions">
                        <button class="complete-btn" onclick="updateOrderStatus(${order.id}, 'Tamamlandı')">Tamamlandı</button>
                        <button class="cancel-btn" onclick="updateOrderStatus(${order.id}, 'İptal Edildi')">İptal Et</button>
                    </div>
                `;
                container.appendChild(orderDiv);
            }
        }
        
        // Sipariş durumunu güncelle
        function updateOrderStatus(orderId, status) {
            fetch(`/api/order/${orderId}/status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: status
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(`Sipariş #${orderId} durumu "${status}" olarak güncellendi.`, 'success');
                    fetchOrders(); // Siparişleri yenile
                } else {
                    showMessage(data.error || 'Sipariş durumu güncellenirken bir hata oluştu.', 'error');
                }
            })
            .catch(error => {
                console.error('Sipariş güncelleme hatası:', error);
                showMessage('Sipariş durumu güncellenirken bir hata oluştu.', 'error');
            });
        }
        
        // Mesaj göster
        function showMessage(message, type) {
            const messageDiv = document.getElementById('status-message');
            messageDiv.textContent = message;
            messageDiv.className = type === 'success' ? 'success' : 'error';
            messageDiv.style.display = 'block';
            
            // 5 saniye sonra mesajı gizle
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>'''
    
    file_path = os.path.join(TEMPLATES_DIR, 'admin.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(admin_html)

# Initialize and run the application
if __name__ == '__main__':
    # Create template files if they don't exist
    create_index_html()
    create_admin_html()
    
    print("\n===== Web Server Başlatıldı =====")
    print("Server aşağıdaki adreslerde çalışıyor:")
    print("1. http://localhost:5000")
    print("2. http://[bilgisayarınızın-IP-adresi]:5000")
    print("==================================\n")
    
    # Start the web server
    app.run(host='0.0.0.0', port=5000, debug=True) 