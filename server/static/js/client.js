document.addEventListener('DOMContentLoaded', () => {
    // Socket connection
    const socket = io();
    
    // Global variables
    let cartItems = {};
    let productPrices = {};
    let stockStatus = {};
    let frequentOrders = {};
    
    // DOM elements
    const frequentOrdersModal = new bootstrap.Modal(document.getElementById('frequentOrdersModal'));
    const addFrequentOrderModal = new bootstrap.Modal(document.getElementById('addFrequentOrderModal'));
    const serverNoteModal = new bootstrap.Modal(document.getElementById('serverNoteModal'));
    
    const cart = document.getElementById('cart');
    const orderNote = document.getElementById('order-note');
    const charCount = document.getElementById('char-count');
    const totalPrice = document.getElementById('total-price');
    const frequentOrdersList = document.getElementById('frequent-orders-list');
    const serverNoteContent = document.getElementById('server-note-content');
    
    // Tea section
    const largeTea = document.getElementById('large-tea');
    const teaButton = document.getElementById('tea-button');
    
    // Coffee section
    const coffeeType = document.getElementById('coffee-type');
    const dubleCoffee = document.getElementById('duble-coffee');
    const dupleLessGrounds = document.getElementById('duble-less-grounds');
    const coffeeButton = document.getElementById('coffee-button');
    
    // Oralet section
    const oraletType = document.getElementById('oralet-type');
    const oraletButton = document.getElementById('oralet-button');
    
    // Other drinks
    const otherDrinkButtons = document.querySelectorAll('.other-drink');
    
    // Cart buttons
    const deleteItemButton = document.getElementById('delete-item');
    const clearCartButton = document.getElementById('clear-cart');
    const sendOrderButton = document.getElementById('send-order');
    
    // Frequent orders
    const viewFrequentOrdersButton = document.getElementById('view-frequent-orders');
    const addFrequentOrderButton = document.getElementById('add-frequent-order');
    const saveFrequentOrderButton = document.getElementById('save-frequent-order');
    
    // Initialize
    init();
    
    function init() {
        // Set up event listeners
        setupEventListeners();
        
        // Update character count
        updateCharCount();
        
        // Register with server
        registerWithServer();
    }
    
    function registerWithServer() {
        socket.emit('register_client', {
            type: 'customer',
            room: room,
            person: person
        });
    }
    
    function setupEventListeners() {
        // Tea button
        teaButton.addEventListener('click', () => {
            const teaType = largeTea.checked ? 'Büyük Çay' : 'Çay';
            addToCart(teaType);
        });
        
        // Coffee button
        coffeeButton.addEventListener('click', () => {
            addToCart(createCoffeeOrder());
        });
        
        // Oralet button
        oraletButton.addEventListener('click', () => {
            const oraletName = `Oralet (${oraletType.value})`;
            addToCart(oraletName);
        });
        
        // Other drinks
        otherDrinkButtons.forEach(button => {
            button.addEventListener('click', () => {
                addToCart(button.dataset.product);
            });
        });
        
        // Cart management
        deleteItemButton.addEventListener('click', deleteSelectedItem);
        clearCartButton.addEventListener('click', clearCart);
        
        // Order management
        sendOrderButton.addEventListener('click', sendOrder);
        
        // Note character count
        orderNote.addEventListener('input', updateCharCount);
        
        // Frequent orders
        viewFrequentOrdersButton.addEventListener('click', showFrequentOrders);
        addFrequentOrderButton.addEventListener('click', () => addFrequentOrderModal.show());
        saveFrequentOrderButton.addEventListener('click', saveFrequentOrder);
        
        // Prevent multiple coffee options
        dubleCoffee.addEventListener('change', updateCoffeeCheckboxes);
        dupleLessGrounds.addEventListener('change', updateCoffeeCheckboxes);
        
        // Socket events
        socket.on('prices_updated', handlePricesUpdate);
        socket.on('stock_updated', handleStockUpdate);
        socket.on('note_updated', handleNoteUpdate);
        socket.on('order_status_updated', handleOrderStatusUpdate);
    }
    
    function createCoffeeOrder() {
        const type = coffeeType.value;
        if (dupleLessGrounds.checked) {
            return `Duble Az Telveli Kahve (${type})`;
        } else if (dubleCoffee.checked) {
            return `Duble Kahve (${type})`;
        }
        return `Kahve (${type})`;
    }
    
    function updateCoffeeCheckboxes() {
        if (dupleLessGrounds.checked) {
            dubleCoffee.checked = false;
        } else if (dubleCoffee.checked) {
            dupleLessGrounds.checked = false;
        }
    }
    
    function addToCart(productName) {
        // Check if product is in stock
        if (stockStatus[productName] === false) {
            alert(`Üzgünüz, ${productName} şu an stokta bulunmamaktadır.`);
            return;
        }
        
        if (cartItems[productName]) {
            cartItems[productName].quantity += 1;
        } else {
            if (!productPrices[productName]) {
                console.error(`Fiyat bulunamadı: ${productName}`);
                return;
            }
            cartItems[productName] = {
                price: productPrices[productName],
                quantity: 1
            };
        }
        
        updateCartDisplay();
        updateTotalPrice();
    }
    
    function updateCartDisplay() {
        cart.innerHTML = '';
        
        Object.entries(cartItems).forEach(([productName, info]) => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.textContent = `${info.quantity} x ${productName}`;
            item.dataset.product = productName;
            
            item.addEventListener('click', (e) => {
                // Remove active class from all items
                document.querySelectorAll('#cart .list-group-item').forEach(
                    el => el.classList.remove('active')
                );
                
                // Add active class to clicked item
                e.target.classList.add('active');
            });
            
            cart.appendChild(item);
        });
    }
    
    function updateTotalPrice() {
        let total = 0;
        Object.values(cartItems).forEach(item => {
            total += item.price * item.quantity;
        });
        
        totalPrice.textContent = `${total.toFixed(2)} ₺`;
    }
    
    function deleteSelectedItem() {
        const selected = document.querySelector('#cart .list-group-item.active');
        if (selected) {
            const productName = selected.dataset.product;
            delete cartItems[productName];
            updateCartDisplay();
            updateTotalPrice();
        } else {
            alert('Lütfen önce bir öğe seçin.');
        }
    }
    
    function clearCart() {
        cartItems = {};
        updateCartDisplay();
        updateTotalPrice();
    }
    
    function updateCharCount() {
        const text = orderNote.value;
        const count = text.length;
        charCount.textContent = `Karakter: ${count}/120`;
        
        // Check line count
        const lines = text.split('\n');
        if (lines.length > 3) {
            orderNote.value = lines.slice(0, 3).join('\n');
            // Recount after adjustment
            const newCount = orderNote.value.length;
            charCount.textContent = `Karakter: ${newCount}/120`;
        }
        
        // Highlight if over limit
        if (count > 120) {
            charCount.style.color = 'red';
        } else {
            charCount.style.color = '';
        }
    }
    
    function sendOrder() {
        if (Object.keys(cartItems).length === 0) {
            alert('Sepetiniz boş. Lütfen önce ürün ekleyin.');
            return;
        }
        
        const note = orderNote.value.trim();
        
        if (note.length > 120) {
            alert('Not 120 karakterden fazla olamaz.');
            return;
        }
        
        // Prepare order string
        const orderString = Object.entries(cartItems)
            .map(([product, info]) => `${info.quantity} x ${product}`)
            .join('\n');
        
        // Calculate total price as a number
        let totalPriceValue = 0;
        Object.entries(cartItems).forEach(([product, info]) => {
            totalPriceValue += info.price * info.quantity;
        });
        
        // Send order to server
        fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order: orderString,
                note: note,
                total_price: totalPriceValue
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Siparişiniz başarıyla gönderildi!');
                clearCart();
                orderNote.value = '';
                updateCharCount();
                
                // Bakiyeyi güncelle
                if (data.balance !== undefined) {
                    document.getElementById('user-balance').textContent = data.balance.toFixed(2) + ' ₺';
                }
            } else {
                // Check if items are out of stock
                if (data.out_of_stock && data.out_of_stock.length > 0) {
                    alert(`Aşağıdaki ürünler stokta yok: ${data.out_of_stock.join(', ')}`);
                } else {
                    alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
                }
            }
        })
        .catch(error => {
            console.error('Error sending order:', error);
            alert('Sipariş gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
        });
    }
    
    function showFrequentOrders() {
        // Fetch frequent orders from server
        fetch('/api/frequent-orders')
            .then(response => response.json())
            .then(orders => {
                frequentOrders = orders;
                
                // Clear existing items
                frequentOrdersList.innerHTML = '';
                
                // Add orders to list
                Object.keys(frequentOrders).forEach(orderName => {
                    const item = document.createElement('button');
                    item.className = 'list-group-item list-group-item-action';
                    item.textContent = orderName;
                    item.addEventListener('click', () => loadFrequentOrder(orderName));
                    frequentOrdersList.appendChild(item);
                });
                
                // Show modal
                frequentOrdersModal.show();
            })
            .catch(error => {
                console.error('Error fetching frequent orders:', error);
                alert('Sık siparişler yüklenirken bir hata oluştu.');
            });
    }
    
    function loadFrequentOrder(orderName) {
        const order = frequentOrders[orderName];
        
        // Clear current cart
        cartItems = {};
        
        // Add items to cart
        Object.entries(order.items).forEach(([product, quantity]) => {
            cartItems[product] = {
                price: productPrices[product],
                quantity: quantity
            };
        });
        
        // Update note
        orderNote.value = order.note || '';
        
        // Update UI
        updateCartDisplay();
        updateTotalPrice();
        updateCharCount();
        
        // Close modal
        frequentOrdersModal.hide();
    }
    
    function saveFrequentOrder() {
        const orderName = document.getElementById('frequent-order-name').value.trim();
        
        if (!orderName) {
            alert('Lütfen sipariş için bir isim girin.');
            return;
        }
        
        if (Object.keys(cartItems).length === 0) {
            alert('Sepetiniz boş. Lütfen önce ürün ekleyin.');
            addFrequentOrderModal.hide();
            return;
        }
        
        // Create order object
        const order = {
            items: {},
            note: orderNote.value.trim()
        };
        
        // Add items to order
        Object.entries(cartItems).forEach(([product, info]) => {
            order.items[product] = info.quantity;
        });
        
        // Save to server
        fetch('/api/frequent-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: orderName,
                order: order
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(`"${orderName}" sık siparişlere eklendi.`);
                addFrequentOrderModal.hide();
            } else {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
            }
        })
        .catch(error => {
            console.error('Error saving frequent order:', error);
            alert('Sık sipariş kaydedilirken bir hata oluştu.');
        });
    }
    
    // Event handlers for socket updates
    function handlePricesUpdate(prices) {
        productPrices = prices;
        console.log('Prices updated:', prices);
        
        // Update cart prices if needed
        Object.keys(cartItems).forEach(product => {
            if (productPrices[product]) {
                cartItems[product].price = productPrices[product];
            }
        });
        
        updateTotalPrice();
    }
    
    function handleStockUpdate(stock) {
        stockStatus = stock;
        console.log('Stock updated:', stock);
        
        // Update product buttons based on stock
        updateProductButtonsState();
    }
    
    function updateProductButtonsState() {
        // Tea button
        const teaType = largeTea.checked ? 'Büyük Çay' : 'Çay';
        updateButtonState(teaButton, teaType, stockStatus[teaType] !== false);
        
        // Coffee button (don't disable, just check when clicked)
        
        // Oralet button
        const oraletName = `Oralet (${oraletType.value})`;
        updateButtonState(oraletButton, oraletName, stockStatus[oraletName] !== false);
        
        // Other drinks
        otherDrinkButtons.forEach(button => {
            const product = button.dataset.product;
            updateButtonState(button, product, stockStatus[product] !== false);
        });
    }
    
    function updateButtonState(button, product, isActive) {
        if (isActive) {
            button.classList.remove('btn-disabled');
            button.disabled = false;
        } else {
            button.classList.add('btn-disabled');
            button.disabled = true;
        }
    }
    
    function handleNoteUpdate(data) {
        const note = data.server_note;
        if (note && note.trim() !== '') {
            serverNoteContent.textContent = note;
            serverNoteModal.show();
        }
    }
    
    function handleOrderStatusUpdate(data) {
        if (data.room === room && data.person === person) {
            if (data.status === 'Tamamlandı') {
                alert('Siparişiniz hazır! Lütfen alınız.');
            } else if (data.status === 'İptal Edildi') {
                // Eğer sipariş iptal edildiyse ve yeni bakiye bilgisi varsa, bakiyeyi güncelle
                if (data.new_balance !== undefined) {
                    document.getElementById('user-balance').textContent = data.new_balance.toFixed(2) + ' ₺';
                    alert(`Siparişiniz iptal edildi. Bakiyeniz iade edildi. Sebep: ${data.reason || 'Belirtilmedi'}`);
                } else {
                    alert(`Siparişiniz iptal edildi. Sebep: ${data.reason || 'Belirtilmedi'}`);
                }
            }
        }
    }
}); 