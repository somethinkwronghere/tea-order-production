document.addEventListener('DOMContentLoaded', () => {
    // Socket connection
    const socket = io();
    
    // Global variables
    let activeOrders = [];
    let productPrices = {};
    let stockStatus = {};
    let computers = [];
    let rooms = {};
    let currentOrderToCancel = null;
    let roomColors = {}; // Oda renklerini saklamak için
    let isMergeModeActive = false; // Birleştirme modu durumu
    
    // Renk paleti - her oda için farklı renk
    const colorPalette = [
        '#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ff99ff', 
        '#99ffff', '#ffcc99', '#cc99ff', '#ccff99', '#ff99cc',
        '#99ccff', '#ffcc99', '#cc99ff', '#99ffcc', '#ff9999'
    ];
    
    // DOM elements
    const adminMenuModal = new bootstrap.Modal(document.getElementById('adminMenuModal'));
    const managePricesModal = new bootstrap.Modal(document.getElementById('managePricesModal'));
    const manageStockModal = new bootstrap.Modal(document.getElementById('manageStockModal'));
    const manageComputersModal = new bootstrap.Modal(document.getElementById('manageComputersModal'));
    const manageRoomsModal = new bootstrap.Modal(document.getElementById('manageRoomsModal'));
    const manageNoteModal = new bootstrap.Modal(document.getElementById('manageNoteModal'));
    const orderHistoryModal = new bootstrap.Modal(document.getElementById('orderHistoryModal'));
    const cancelReasonModal = new bootstrap.Modal(document.getElementById('cancelReasonModal'));
    const logsModal = new bootstrap.Modal(document.getElementById('logsModal'));
    
    const showAdminMenuButton = document.getElementById('show-admin-menu');
    const managePricesButton = document.getElementById('manage-prices-btn');
    const manageStockButton = document.getElementById('manage-stock-btn');
    const manageComputersButton = document.getElementById('manage-computers-btn');
    const manageRoomsButton = document.getElementById('manage-rooms-btn');
    const manageNoteButton = document.getElementById('manage-note-btn');
    const viewOrderHistoryButton = document.getElementById('view-order-history-btn');
    const viewLogsButton = document.getElementById('view-logs-btn');
    const orderMergeModeToggle = document.getElementById('order-merge-mode');
    
    const activeOrdersContainer = document.getElementById('active-orders');
    const noOrdersMessage = document.getElementById('no-orders-message');
    
    const pricesTableBody = document.getElementById('prices-table-body');
    const savePricesButton = document.getElementById('save-prices');
    
    const stockTableBody = document.getElementById('stock-table-body');
    const saveStockButton = document.getElementById('save-stock');
    
    const newComputerName = document.getElementById('new-computer-name');
    const addComputerButton = document.getElementById('add-computer');
    const computersList = document.getElementById('computers-list');
    
    const newRoomName = document.getElementById('new-room-name');
    const addRoomButton = document.getElementById('add-room');
    const roomsList = document.getElementById('rooms-list');
    
    const serverNoteTextarea = document.getElementById('server-note');
    const saveNoteButton = document.getElementById('save-note');
    
    const orderHistoryTableBody = document.getElementById('order-history-table-body');
    
    const cancelReasonTextarea = document.getElementById('cancel-reason');
    const confirmCancelButton = document.getElementById('confirm-cancel');
    
    // Initialize
    init();
    
    function init() {
        // Register with server
        socket.emit('register_client', {
            type: 'admin'
        });
        
        // Set up event listeners
        setupEventListeners();
        
        // Load active orders
        loadActiveOrders();
        
        // Load initial data
        loadInitialData();
    }
    
    function setupEventListeners() {
        // Admin menu
        showAdminMenuButton.addEventListener('click', () => adminMenuModal.show());
        managePricesButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showManagePrices();
        });
        manageStockButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showManageStock();
        });
        manageComputersButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showManageComputers();
        });
        manageRoomsButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showManageRooms();
        });
        manageNoteButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showManageNote();
        });
        viewOrderHistoryButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showOrderHistory();
        });
        viewLogsButton.addEventListener('click', () => {
            adminMenuModal.hide();
            showLogs();
        });
        
        // Order merge mode toggle
        orderMergeModeToggle.addEventListener('change', function() {
            isMergeModeActive = this.checked;
            displayActiveOrders(); // Sipariş görünümünü güncelle
        });
        
        // Save buttons
        savePricesButton.addEventListener('click', savePrices);
        saveStockButton.addEventListener('click', saveStock);
        saveNoteButton.addEventListener('click', saveNote);
        
        // Computer management
        addComputerButton.addEventListener('click', addComputer);
        
        // Room management
        addRoomButton.addEventListener('click', addRoom);
        
        // Cancel order confirmation
        confirmCancelButton.addEventListener('click', confirmCancelOrder);
        
        // Socket events
        socket.on('new_order', handleNewOrder);
        socket.on('active_orders', handleActiveOrders);
    }
    
    function loadInitialData() {
        // Load prices
        fetch('/api/prices')
            .then(response => response.json())
            .then(prices => {
                productPrices = prices;
            })
            .catch(error => console.error('Error loading prices:', error));
        
        // Load stock status
        fetch('/api/stock')
            .then(response => response.json())
            .then(stock => {
                stockStatus = stock;
            })
            .catch(error => console.error('Error loading stock:', error));
        
        // Load computers
        fetch('/api/computers')
            .then(response => response.json())
            .then(data => {
                computers = data;
            })
            .catch(error => console.error('Error loading computers:', error));
        
        // Load rooms
        fetch('/api/rooms')
            .then(response => response.json())
            .then(data => {
                rooms = data;
                // Her oda için bir renk atama
                assignColorsToRooms();
            })
            .catch(error => console.error('Error loading rooms:', error));
        
        // Load server note
        fetch('/api/note')
            .then(response => response.json())
            .then(data => {
                serverNoteTextarea.value = data.server_note || '';
            })
            .catch(error => console.error('Error loading note:', error));
    }
    
    // Her oda için renk atama fonksiyonu
    function assignColorsToRooms() {
        let colorIndex = 0;
        Object.keys(rooms).forEach(roomName => {
            roomColors[roomName] = colorPalette[colorIndex % colorPalette.length];
            colorIndex++;
        });
    }
    
    function loadActiveOrders() {
        socket.emit('get_active_orders');
        
        // Also fetch from API as backup
        fetch('/api/orders')
            .then(response => response.json())
            .then(orders => {
                if (!activeOrders.length) {
                    handleActiveOrders(orders);
                }
            })
            .catch(error => console.error('Error loading orders:', error));
    }
    
    // Admin functions
    function showManagePrices() {
        // Clear existing items
        pricesTableBody.innerHTML = '';
        
        // Add products to table
        Object.entries(productPrices).forEach(([product, price]) => {
            const row = document.createElement('tr');
            
            const productCell = document.createElement('td');
            productCell.textContent = product;
            row.appendChild(productCell);
            
            const priceCell = document.createElement('td');
            const priceInput = document.createElement('input');
            priceInput.type = 'number';
            priceInput.className = 'form-control price-input';
            priceInput.min = '0';
            priceInput.step = '0.5';
            priceInput.value = price;
            priceInput.dataset.product = product;
            priceCell.appendChild(priceInput);
            row.appendChild(priceCell);
            
            pricesTableBody.appendChild(row);
        });
        
        // Show modal
        managePricesModal.show();
    }
    
    function savePrices() {
        // Get all price inputs
        const priceInputs = document.querySelectorAll('.price-input');
        
        // Update prices object
        const updatedPrices = {};
        priceInputs.forEach(input => {
            const product = input.dataset.product;
            const price = parseFloat(input.value);
            updatedPrices[product] = price;
        });
        
        // Save to server
        fetch('/api/prices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedPrices)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Fiyatlar başarıyla güncellendi!');
                productPrices = updatedPrices;
                managePricesModal.hide();
            } else {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
            }
        })
        .catch(error => {
            console.error('Error saving prices:', error);
            alert('Fiyatlar kaydedilirken bir hata oluştu.');
        });
    }
    
    function showManageStock() {
        // Clear existing items
        stockTableBody.innerHTML = '';
        
        // Add products to table
        Object.keys(productPrices).forEach(product => {
            const row = document.createElement('tr');
            
            const productCell = document.createElement('td');
            productCell.textContent = product;
            row.appendChild(productCell);
            
            const statusCell = document.createElement('td');
            const statusSwitch = document.createElement('div');
            statusSwitch.className = 'form-check form-switch';
            
            const statusInput = document.createElement('input');
            statusInput.className = 'form-check-input stock-status';
            statusInput.type = 'checkbox';
            statusInput.id = `stock-${product}`;
            statusInput.dataset.product = product;
            statusInput.checked = stockStatus[product] !== false;
            
            const statusLabel = document.createElement('label');
            statusLabel.className = 'form-check-label';
            statusLabel.htmlFor = `stock-${product}`;
            statusLabel.textContent = statusInput.checked ? 'Var' : 'Yok';
            
            // Update label when switch changes
            statusInput.addEventListener('change', (e) => {
                statusLabel.textContent = e.target.checked ? 'Var' : 'Yok';
            });
            
            statusSwitch.appendChild(statusInput);
            statusSwitch.appendChild(statusLabel);
            statusCell.appendChild(statusSwitch);
            row.appendChild(statusCell);
            
            stockTableBody.appendChild(row);
        });
        
        // Show modal
        manageStockModal.show();
    }
    
    function saveStock() {
        // Get all stock status inputs
        const stockInputs = document.querySelectorAll('.stock-status');
        
        // Update stock status object
        const updatedStock = {};
        stockInputs.forEach(input => {
            const product = input.dataset.product;
            const isActive = input.checked;
            updatedStock[product] = isActive;
        });
        
        // Save to server
        fetch('/api/stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedStock)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Stok durumu başarıyla güncellendi!');
                stockStatus = updatedStock;
                manageStockModal.hide();
            } else {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
            }
        })
        .catch(error => {
            console.error('Error saving stock status:', error);
            alert('Stok durumu kaydedilirken bir hata oluştu.');
        });
    }
    
    function showManageComputers() {
        // Update computer list
        updateComputersList();
        
        // Show modal
        manageComputersModal.show();
    }
    
    function updateComputersList() {
        // Clear existing items
        computersList.innerHTML = '';
        
        // Add computers to list
        computers.forEach(computer => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = computer;
            item.appendChild(nameSpan);
            
            const buttonsDiv = document.createElement('div');
            
            const editButton = document.createElement('button');
            editButton.className = 'btn btn-sm btn-warning me-2';
            editButton.textContent = 'Düzenle';
            editButton.addEventListener('click', () => editComputer(computer));
            buttonsDiv.appendChild(editButton);
            
            const deleteButton = document.createElement('button');
            deleteButton.className = 'btn btn-sm btn-danger';
            deleteButton.textContent = 'Sil';
            deleteButton.addEventListener('click', () => removeComputer(computer));
            buttonsDiv.appendChild(deleteButton);
            
            item.appendChild(buttonsDiv);
            
            computersList.appendChild(item);
        });
    }
    
    function addComputer() {
        const name = newComputerName.value.trim();
        
        if (!name) {
            alert('Lütfen bilgisayar adı girin.');
            return;
        }
        
        if (computers.includes(name)) {
            alert('Bu bilgisayar zaten eklenmiş.');
            return;
        }
        
        // Add to computers array
        computers.push(name);
        
        // Save to server
        saveComputers();
        
        // Clear input
        newComputerName.value = '';
        
        // Update list
        updateComputersList();
    }
    
    function removeComputer(computer) {
        if (confirm(`"${computer}" bilgisayarını silmek istediğinizden emin misiniz?`)) {
            // Remove from computers array
            computers = computers.filter(c => c !== computer);
            
            // Save to server
            saveComputers();
            
            // Update list
            updateComputersList();
        }
    }
    
    function editComputer(oldName) {
        const newName = prompt('Yeni isim:', oldName);
        
        if (newName && newName.trim() && newName !== oldName) {
            if (computers.includes(newName)) {
                alert('Bu isim zaten kullanılıyor.');
                return;
            }
            
            // Update in computers array
            const index = computers.indexOf(oldName);
            if (index !== -1) {
                computers[index] = newName;
                
                // Save to server
                saveComputers();
                
                // Update list
                updateComputersList();
            }
        }
    }
    
    function saveComputers() {
        fetch('/api/computers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({computers: computers})
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
            }
        })
        .catch(error => {
            console.error('Error saving computers:', error);
            alert('Bilgisayarlar kaydedilirken bir hata oluştu.');
        });
    }
    
    function showManageRooms() {
        // Update room list
        updateRoomsList();
        
        // Show modal
        manageRoomsModal.show();
    }
    
    function updateRoomsList() {
        // Clear existing items
        roomsList.innerHTML = '';
        
        // Add rooms to list
        Object.keys(rooms).forEach(roomName => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            // Oda için renk uygulaması
            if (roomColors[roomName]) {
                item.style.backgroundColor = roomColors[roomName];
                item.style.borderLeft = `5px solid ${adjustColor(roomColors[roomName], -30)}`;
            }
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = roomName;
            item.appendChild(nameSpan);
            
            const buttonsDiv = document.createElement('div');
            
            // Edit button
            const editButton = document.createElement('button');
            editButton.className = 'btn btn-sm btn-primary me-2';
            editButton.textContent = 'Düzenle';
            editButton.addEventListener('click', () => editRoom(roomName));
            buttonsDiv.appendChild(editButton);
            
            // Delete button
            const deleteButton = document.createElement('button');
            deleteButton.className = 'btn btn-sm btn-danger';
            deleteButton.textContent = 'Sil';
            deleteButton.addEventListener('click', () => removeRoom(roomName));
            buttonsDiv.appendChild(deleteButton);
            
            item.appendChild(buttonsDiv);
            
            roomsList.appendChild(item);
        });
    }
    
    // Rengi koyulaştırma/açma fonksiyonu
    function adjustColor(color, amount) {
        return '#' + color.replace(/^#/, '').replace(/../g, color => ('0'+Math.min(255, Math.max(0, parseInt(color, 16) + amount)).toString(16)).substr(-2));
    }
    
    function addRoom() {
        const name = newRoomName.value.trim();
        
        if (!name) {
            alert('Lütfen oda adı girin.');
            return;
        }
        
        if (rooms[name]) {
            alert('Bu oda zaten eklenmiş.');
            return;
        }
        
        // Create room with 4 default persons
        rooms[name] = ["kişi1", "kişi2", "kişi3", "kişi4"];
        
        // Odaya renk ata
        roomColors[name] = colorPalette[Object.keys(rooms).length % colorPalette.length];
        
        // Save to server
        saveRooms();
        
        // Clear input
        newRoomName.value = '';
        
        // Update list
        updateRoomsList();
    }
    
    function editRoom(roomName) {
        // Create modal for editing room persons
        const modalHtml = `
        <div class="modal fade" id="editRoomModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">"${roomName}" Odasını Düzenle</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Kişi İsimleri:</label>
                            <div id="person-inputs"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">İptal</button>
                        <button type="button" id="save-room-edit" class="btn btn-primary">Kaydet</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        // Add modal to document
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);
        
        // Get modal element
        const editModal = document.getElementById('editRoomModal');
        const modal = new bootstrap.Modal(editModal);
        
        // Get persons for this room
        const persons = rooms[roomName];
        
        // Create input fields for each person
        const personInputs = document.getElementById('person-inputs');
        persons.forEach((person, index) => {
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group mb-2';
            
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control person-input';
            input.value = person;
            input.dataset.index = index;
            inputGroup.appendChild(input);
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-outline-danger';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', () => {
                inputGroup.remove();
            });
            inputGroup.appendChild(removeBtn);
            
            personInputs.appendChild(inputGroup);
        });
        
        // Add button to add new person
        const addPersonBtn = document.createElement('button');
        addPersonBtn.className = 'btn btn-sm btn-outline-primary mt-2';
        addPersonBtn.textContent = 'Kişi Ekle';
        addPersonBtn.addEventListener('click', () => {
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group mb-2';
            
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control person-input';
            input.value = `kişi${persons.length + 1}`;
            input.dataset.index = persons.length;
            inputGroup.appendChild(input);
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-outline-danger';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', () => {
                inputGroup.remove();
            });
            inputGroup.appendChild(removeBtn);
            
            personInputs.appendChild(inputGroup);
        });
        personInputs.appendChild(addPersonBtn);
        
        // Save button event
        document.getElementById('save-room-edit').addEventListener('click', () => {
            const inputs = document.querySelectorAll('.person-input');
            const newPersons = [];
            
            inputs.forEach(input => {
                const value = input.value.trim();
                if (value) {
                    newPersons.push(value);
                }
            });
            
            if (newPersons.length === 0) {
                alert('En az bir kişi olmalıdır.');
                return;
            }
            
            // Update room
            rooms[roomName] = newPersons;
            
            // Save to server
            saveRooms();
            
            // Close modal
            modal.hide();
            editModal.addEventListener('hidden.bs.modal', () => {
                modalContainer.remove();
            });
            
            // Update list
            updateRoomsList();
        });
        
        // Show modal
        modal.show();
    }
    
    function removeRoom(roomName) {
        if (confirm(`"${roomName}" odasını silmek istediğinizden emin misiniz?`)) {
            // Remove from rooms object
            delete rooms[roomName];
            delete roomColors[roomName];
            
            // Save to server
            saveRooms();
            
            // Update list
            updateRoomsList();
        }
    }
    
    function saveRooms() {
        fetch('/api/rooms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rooms: rooms
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
            }
        })
        .catch(error => {
            console.error('Error saving rooms:', error);
            alert('Odalar kaydedilirken bir hata oluştu.');
        });
    }
    
    function showManageNote() {
        // Show modal
        manageNoteModal.show();
    }
    
    function saveNote() {
        const note = serverNoteTextarea.value.trim();
        
        // Save to server
        fetch('/api/note', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                server_note: note
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Sunucu notu başarıyla güncellendi!');
                manageNoteModal.hide();
            } else {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
            }
        })
        .catch(error => {
            console.error('Error saving note:', error);
            alert('Sunucu notu kaydedilirken bir hata oluştu.');
        });
    }
    
    function showOrderHistory() {
        // Fetch order history from Excel file
        fetch('/api/order-history')
            .then(response => response.json())
            .then(orders => {
                // Clear existing items
                orderHistoryTableBody.innerHTML = '';
                
                // Add orders to table
                orders.forEach(order => {
                    const row = document.createElement('tr');
                    
                    // Oda için renk uygulaması
                    if (roomColors[order.room]) {
                        row.style.backgroundColor = adjustColor(roomColors[order.room], 50); // Daha açık ton
                    }
                    
                    const timeCell = document.createElement('td');
                    timeCell.textContent = order.order_time;
                    row.appendChild(timeCell);
                    
                    const clientCell = document.createElement('td');
                    clientCell.textContent = `${order.room} - ${order.person}`;
                    row.appendChild(clientCell);
                    
                    const orderCell = document.createElement('td');
                    orderCell.innerHTML = order.order.replace(/\n/g, '<br>');
                    row.appendChild(orderCell);
                    
                    const noteCell = document.createElement('td');
                    noteCell.textContent = order.note;
                    row.appendChild(noteCell);
                    
                    const statusCell = document.createElement('td');
                    statusCell.textContent = order.status;
                    row.appendChild(statusCell);
                    
                    const deliveryCell = document.createElement('td');
                    deliveryCell.textContent = order.delivery_time || '';
                    row.appendChild(deliveryCell);
                    
                    orderHistoryTableBody.appendChild(row);
                });
                
                // Show modal
                orderHistoryModal.show();
            })
            .catch(error => {
                console.error('Error fetching order history:', error);
                alert('Sipariş geçmişi yüklenirken bir hata oluştu.');
            });
    }
    
    // Order management functions
    function handleNewOrder(order) {
        // Add to active orders
        activeOrders.push(order);
        
        // Hide no orders message
        noOrdersMessage.style.display = 'none';
        
        // Display order
        displayActiveOrders();
        
        // Play notification sound
        playOrderSound();
    }
    
    function handleActiveOrders(orders) {
        activeOrders = orders;
        
        // Show/hide no orders message
        if (activeOrders.length === 0) {
            noOrdersMessage.style.display = 'block';
        } else {
            noOrdersMessage.style.display = 'none';
        }
        
        // Display orders
        displayActiveOrders();
    }
    
    function displayActiveOrders() {
        // Clear existing orders
        activeOrdersContainer.innerHTML = '';
        
        // If no orders, show message
        if (activeOrders.length === 0) {
            activeOrdersContainer.appendChild(noOrdersMessage);
            return;
        }
        
        if (isMergeModeActive) {
            // Birleştirme modu aktif - Aynı odadan gelen siparişleri grupla
            displayMergedOrders();
        } else {
            // Normal mod - Tüm siparişleri ayrı ayrı göster
            activeOrders.forEach(order => {
                addOrderToDisplay(order);
            });
        }
    }
    
    function displayMergedOrders() {
        // Önce siparişleri oda bazında grupla
        const ordersByRoom = {};
        
        activeOrders.forEach(order => {
            if (!ordersByRoom[order.room]) {
                ordersByRoom[order.room] = [];
            }
            ordersByRoom[order.room].push(order);
        });
        
        // Her oda için birleştirilmiş sipariş oluştur
        Object.keys(ordersByRoom).forEach(room => {
            const roomOrders = ordersByRoom[room];
            
            // Eğer odada sadece 1 sipariş varsa normal göster
            if (roomOrders.length === 1) {
                addOrderToDisplay(roomOrders[0]);
                return;
            }
            
            // Birden fazla sipariş varsa birleştir
            createMergedOrderCard(room, roomOrders);
        });
    }
    
    function createMergedOrderCard(room, orders) {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-4';
        col.id = `room-orders-${room}`;
        
        const card = document.createElement('div');
        card.className = 'card order-card blinking-room'; // Yanıp sönme efekti
        
        // Odaya özel renk
        if (roomColors[room]) {
            card.style.borderLeft = `5px solid ${roomColors[room]}`;
            card.style.borderRight = `5px solid ${roomColors[room]}`;
        }
        
        // Card header
        const header = document.createElement('div');
        header.className = 'card-header';
        header.innerHTML = `<h5>Oda: ${room} <span class="badge bg-warning">${orders.length} Sipariş</span></h5>`;
        card.appendChild(header);
        
        // Card body - siparişleri listele
        const body = document.createElement('div');
        body.className = 'card-body';
        
        // Siparişleri kişi bazında listele
        const personOrders = document.createElement('div');
        
        orders.forEach(order => {
            const orderDetails = document.createElement('div');
            orderDetails.className = 'mb-3 p-2 border-bottom';
            
            const orderHeader = document.createElement('h6');
            orderHeader.innerHTML = `<strong>${order.person}</strong> <small class="text-muted">(${new Date(order.order_time).toLocaleTimeString()})</small>`;
            orderDetails.appendChild(orderHeader);
            
            // Order items
            const orderItems = document.createElement('pre');
            orderItems.className = 'order-items mb-2';
            orderItems.textContent = order.order;
            orderDetails.appendChild(orderItems);
            
            // Notes if any
            if (order.note) {
                const notes = document.createElement('p');
                notes.className = 'mb-1 text-muted';
                notes.innerHTML = `<small><strong>Not:</strong> ${order.note}</small>`;
                orderDetails.appendChild(notes);
            }
            
            // Price
            const price = document.createElement('p');
            price.className = 'mb-0 text-end';
            price.innerHTML = `<strong>Tutar:</strong> ${order.total_price.toFixed(2)} ₺`;
            orderDetails.appendChild(price);
            
            personOrders.appendChild(orderDetails);
        });
        
        body.appendChild(personOrders);
        card.appendChild(body);
        
        // Card footer - toplam süre ve butonlar
        const footer = document.createElement('div');
        footer.className = 'card-footer d-flex justify-content-between align-items-center';
        
        // Left side - total time
        const timer = document.createElement('div');
        timer.className = 'order-timer';
        timer.innerHTML = `<span class="badge bg-secondary">En Eski: <span id="timer-${orders[0].order_id}">00:00</span></span>`;
        footer.appendChild(timer);
        
        // Right side - action buttons for all orders
        const actions = document.createElement('div');
        actions.className = 'btn-group';
        
        const completeAllButton = document.createElement('button');
        completeAllButton.className = 'btn btn-success';
        completeAllButton.textContent = 'Tümünü Tamamla';
        completeAllButton.addEventListener('click', () => {
            if (confirm(`${room} odasındaki tüm siparişleri tamamlamak istiyor musunuz?`)) {
                // Count how many orders we need to complete
                const totalOrders = orders.length;
                let completedCount = 0;
                
                // Create a function to track completion
                const trackCompletion = () => {
                    completedCount++;
                    if (completedCount >= totalOrders) {
                        // All orders completed, refresh the page
                        window.location.reload();
                    }
                };
                
                // Update all orders with the tracking function
                orders.forEach(order => {
                    updateOrderStatus(order.order_id, 'Tamamlandı', null, trackCompletion);
                });
            }
        });
        actions.appendChild(completeAllButton);
        
        const cancelAllButton = document.createElement('button');
        cancelAllButton.className = 'btn btn-danger';
        cancelAllButton.textContent = 'Tümünü İptal Et';
        cancelAllButton.addEventListener('click', () => {
            if (confirm(`${room} odasındaki tüm siparişleri iptal etmek istiyor musunuz?`)) {
                const reason = prompt("İptal nedeni:", "");
                if (reason !== null) {
                    // Count how many orders we need to cancel
                    const totalOrders = orders.length;
                    let canceledCount = 0;
                    
                    // Create a function to track cancellation
                    const trackCancellation = () => {
                        canceledCount++;
                        if (canceledCount >= totalOrders) {
                            // All orders canceled, refresh the page
                            window.location.reload();
                        }
                    };
                    
                    // Update all orders with the tracking function
                    orders.forEach(order => {
                        updateOrderStatus(order.order_id, 'İptal Edildi', reason, trackCancellation);
                    });
                }
            }
        });
        actions.appendChild(cancelAllButton);
        
        footer.appendChild(actions);
        card.appendChild(footer);
        
        // Add to container
        col.appendChild(card);
        activeOrdersContainer.appendChild(col);
        
        // Start timer for oldest order
        startOrderTimer(orders[0]);
    }
    
    function updateOrderStatus(orderId, status, reason, callback = null) {
        const data = { status };
        
        if (status === 'İptal Edildi' && reason) {
            data.reason = reason;
        }
        
        // Update status on server
        fetch(`/api/order/${orderId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Remove from active orders if completed or canceled
                if (status === 'Tamamlandı' || status === 'İptal Edildi') {
                    removeOrderFromDisplay(orderId);
                    
                    // Update active orders array
                    activeOrders = activeOrders.filter(order => order.order_id !== orderId);
                    
                    // Show no orders message if needed
                    if (activeOrders.length === 0) {
                        noOrdersMessage.style.display = 'block';
                    }
                }
                
                // Call the callback if provided
                if (callback) {
                    callback();
                }
            } else {
                alert(`Hata: ${data.message || 'Bilinmeyen bir hata oluştu.'}`);
                // Still call the callback to avoid blocking the process
                if (callback) {
                    callback();
                }
            }
        })
        .catch(error => {
            console.error('Error updating order status:', error);
            alert('Sipariş durumu güncellenirken bir hata oluştu.');
            // Still call the callback to avoid blocking the process
            if (callback) {
                callback();
            }
        });
    }
    
    function removeOrderFromDisplay(orderId) {
        const orderElement = document.getElementById(`order-${orderId}`);
        if (orderElement) {
            orderElement.remove();
        }
    }
    
    function showCancelReason(orderId) {
        // Clear previous reason
        cancelReasonTextarea.value = '';
        
        // Store current order to cancel
        currentOrderToCancel = orderId;
        
        // Show modal
        cancelReasonModal.show();
    }
    
    function confirmCancelOrder() {
        if (currentOrderToCancel) {
            const reason = cancelReasonTextarea.value.trim();
            updateOrderStatus(currentOrderToCancel, 'İptal Edildi', reason);
            cancelReasonModal.hide();
            currentOrderToCancel = null;
        }
    }
    
    function startOrderTimer(order) {
        // Calculate elapsed time
        const startTime = order.start_time * 1000; // Convert to milliseconds
        const timerElement = document.getElementById(`timer-${order.order_id}`);
        
        if (!timerElement) return;
        
        // Update timer every second
        const updateTimer = () => {
            const now = Date.now();
            const elapsed = Math.floor((now - startTime) / 1000);
            
            // Format time
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            
            timerElement.textContent = `${minutes}:${seconds}`;
            
            // Add blinking effect after 5 minutes
            if (elapsed > 300) {
                timerElement.parentElement.parentElement.classList.add('blinking');
            }
        };
        
        // Initial update
        updateTimer();
        
        // Set interval
        const timerId = setInterval(updateTimer, 1000);
        
        // Store timer ID to clear it if needed
        timerElement.dataset.timerId = timerId;
    }
    
    function getStatusClass(status) {
        switch (status) {
            case 'Beklemede':
                return 'pending';
            case 'İşleniyor':
                return 'processing';
            case 'Tamamlandı':
                return 'completed';
            case 'İptal Edildi':
                return 'canceled';
            default:
                return 'pending';
        }
    }
    
    // Log functions
    function showLogs() {
        // Sipariş Loglarını Yükle
        fetch('/api/logs/orders')
            .then(response => response.json())
            .then(logs => {
                renderOrderLogs(logs);
            })
            .catch(error => {
                console.error('Error loading order logs:', error);
            });
        
        // Bakiye Transfer Loglarını Yükle
        fetch('/api/logs/balance-transfers')
            .then(response => response.json())
            .then(logs => {
                renderBalanceTransferLogs(logs);
            })
            .catch(error => {
                console.error('Error loading balance transfer logs:', error);
            });
        
        // Bakiye Ekleme Loglarını Yükle
        fetch('/api/logs/balance-additions')
            .then(response => response.json())
            .then(logs => {
                renderBalanceAdditionLogs(logs);
            })
            .catch(error => {
                console.error('Error loading balance addition logs:', error);
            });
        
        // Bakiye Düşme Loglarını Yükle
        fetch('/api/logs/balance-deductions')
            .then(response => response.json())
            .then(logs => {
                renderBalanceDeductionLogs(logs);
            })
            .catch(error => {
                console.error('Error loading balance deduction logs:', error);
            });
        
        // Log modalını göster
        logsModal.show();
    }
    
    function renderOrderLogs(logs) {
        const tbody = document.getElementById('order-logs-body');
        tbody.innerHTML = '';
        
        // En yeni loglar en üstte görüntülensin
        logs.reverse().forEach(log => {
            const row = document.createElement('tr');
            
            // Tarih
            const dateCell = document.createElement('td');
            dateCell.textContent = log.timestamp;
            row.appendChild(dateCell);
            
            // Kullanıcı
            const userCell = document.createElement('td');
            userCell.textContent = `${log.room} - ${log.person}`;
            row.appendChild(userCell);
            
            // Sipariş
            const orderCell = document.createElement('td');
            orderCell.textContent = log.order;
            row.appendChild(orderCell);
            
            // Tutar
            const priceCell = document.createElement('td');
            priceCell.textContent = `${log.total_price.toFixed(2)} ₺`;
            row.appendChild(priceCell);
            
            // Not
            const noteCell = document.createElement('td');
            noteCell.textContent = log.note || '-';
            row.appendChild(noteCell);
            
            tbody.appendChild(row);
        });
    }
    
    function renderBalanceTransferLogs(logs) {
        const tbody = document.getElementById('transfer-logs-body');
        tbody.innerHTML = '';
        
        // En yeni loglar en üstte görüntülensin
        logs.reverse().forEach(log => {
            const row = document.createElement('tr');
            
            // Tarih
            const dateCell = document.createElement('td');
            dateCell.textContent = log.timestamp;
            row.appendChild(dateCell);
            
            // Gönderen
            const fromCell = document.createElement('td');
            fromCell.textContent = log.from_user_id;
            row.appendChild(fromCell);
            
            // Alan
            const toCell = document.createElement('td');
            toCell.textContent = log.to_user_id;
            row.appendChild(toCell);
            
            // Miktar
            const amountCell = document.createElement('td');
            amountCell.textContent = `${log.amount.toFixed(2)} ₺`;
            row.appendChild(amountCell);
            
            tbody.appendChild(row);
        });
    }
    
    function renderBalanceAdditionLogs(logs) {
        const tbody = document.getElementById('add-logs-body');
        tbody.innerHTML = '';
        
        // En yeni loglar en üstte görüntülensin
        logs.reverse().forEach(log => {
            const row = document.createElement('tr');
            
            // Tarih
            const dateCell = document.createElement('td');
            dateCell.textContent = log.timestamp;
            row.appendChild(dateCell);
            
            // Admin
            const adminCell = document.createElement('td');
            adminCell.textContent = log.admin_id;
            row.appendChild(adminCell);
            
            // Kullanıcı
            const userCell = document.createElement('td');
            userCell.textContent = log.user_id;
            row.appendChild(userCell);
            
            // Miktar
            const amountCell = document.createElement('td');
            amountCell.textContent = `${log.amount.toFixed(2)} ₺`;
            row.appendChild(amountCell);
            
            tbody.appendChild(row);
        });
    }
    
    // Add a new function to render balance deduction logs
    function renderBalanceDeductionLogs(logs) {
        const tbody = document.getElementById('deduct-logs-body');
        if (!tbody) {
            console.error('Deduct logs tbody element not found');
            return;
        }
        
        tbody.innerHTML = '';
        
        // En yeni loglar en üstte görüntülensin
        logs.reverse().forEach(log => {
            const row = document.createElement('tr');
            
            // Tarih
            const dateCell = document.createElement('td');
            dateCell.textContent = log.timestamp;
            row.appendChild(dateCell);
            
            // Admin
            const adminCell = document.createElement('td');
            adminCell.textContent = log.admin_id;
            row.appendChild(adminCell);
            
            // Kullanıcı
            const userCell = document.createElement('td');
            userCell.textContent = log.user_id;
            row.appendChild(userCell);
            
            // Miktar
            const amountCell = document.createElement('td');
            amountCell.textContent = `${log.amount.toFixed(2)} ₺`;
            row.appendChild(amountCell);
            
            tbody.appendChild(row);
        });
    }
    
    // Normal mode - individual order display function
    function addOrderToDisplay(order) {
        const col = document.createElement('div');
        col.className = 'col-lg-4 col-md-6 mb-4';
        col.id = `order-${order.order_id}`;
        
        const card = document.createElement('div');
        card.className = `order-card status-${getStatusClass(order.status)}`;
        
        // Oda için renk uygulaması
        if (roomColors[order.room]) {
            card.style.borderRight = `5px solid ${roomColors[order.room]}`;
            card.style.borderTop = `2px solid ${roomColors[order.room]}`;
        }
        
        // Header section
        const header = document.createElement('div');
        header.className = 'card-header';
        
        const clientName = document.createElement('h4');
        clientName.textContent = `${order.room} - ${order.person}`;
        
        // Oda adına ait renk ile yazıyı vurgulama
        if (roomColors[order.room]) {
            clientName.style.color = adjustColor(roomColors[order.room], -50); // Daha koyu ton
            clientName.style.textShadow = "0px 0px 1px rgba(0,0,0,0.2)";
        }
        
        header.appendChild(clientName);
        
        const orderTime = document.createElement('span');
        orderTime.className = 'text-muted d-block small';
        orderTime.textContent = order.order_time;
        header.appendChild(orderTime);
        
        card.appendChild(header);
        
        // Content section
        const content = document.createElement('div');
        content.className = 'card-body';
        
        const orderDetails = document.createElement('div');
        orderDetails.className = 'mb-3';
        orderDetails.innerHTML = `<strong>Sipariş:</strong><br><pre class="order-items">${order.order}</pre>`;
        content.appendChild(orderDetails);
        
        if (order.note) {
            const noteDetails = document.createElement('div');
            noteDetails.className = 'mb-3';
            noteDetails.innerHTML = `<strong>Not:</strong><br>${order.note}`;
            content.appendChild(noteDetails);
        }
        
        const priceDetails = document.createElement('div');
        priceDetails.className = 'text-end';
        priceDetails.innerHTML = `<strong>Toplam:</strong> ${order.total_price.toFixed(2)} ₺`;
        content.appendChild(priceDetails);
        
        card.appendChild(content);
        
        // Footer section
        const footer = document.createElement('div');
        footer.className = 'card-footer d-flex justify-content-between align-items-center';
        
        // Left side - timer
        const timer = document.createElement('div');
        timer.className = 'order-timer';
        timer.innerHTML = `<span class="badge bg-secondary">Süre: <span id="timer-${order.order_id}">00:00</span></span>`;
        footer.appendChild(timer);
        
        // Right side - action buttons
        const actions = document.createElement('div');
        actions.className = 'btn-group';
        
        const completeButton = document.createElement('button');
        completeButton.className = 'btn btn-success';
        completeButton.textContent = 'Tamamlandı';
        completeButton.addEventListener('click', () => updateOrderStatus(order.order_id, 'Tamamlandı'));
        actions.appendChild(completeButton);
        
        const cancelButton = document.createElement('button');
        cancelButton.className = 'btn btn-danger';
        cancelButton.textContent = 'İptal';
        cancelButton.addEventListener('click', () => showCancelReason(order.order_id));
        actions.appendChild(cancelButton);
        
        footer.appendChild(actions);
        
        card.appendChild(footer);
        
        // Add to container
        col.appendChild(card);
        activeOrdersContainer.appendChild(col);
        
        // Start timer
        startOrderTimer(order);
    }
    
    // Notification sound for new orders
    function playOrderSound() {
        try {
            // Create a simple beep sound
            const context = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = context.createOscillator();
            const gain = context.createGain();
            
            oscillator.connect(gain);
            gain.connect(context.destination);
            
            oscillator.type = 'sine';
            oscillator.frequency.value = 800;
            gain.gain.value = 0.5;
            
            oscillator.start(context.currentTime);
            oscillator.stop(context.currentTime + 0.3);
        } catch (error) {
            console.log('Sound notification error:', error);
        }
    }
}); 