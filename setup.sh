#!/bin/bash

# Güncellemeleri yükle
sudo apt update
sudo apt upgrade -y

# Gerekli paketleri yükle
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Proje dizinini oluştur
sudo mkdir -p /var/www/tea-order
sudo chown -R www-data:www-data /var/www/tea-order

# Python virtual environment oluştur
cd /var/www/tea-order
python3 -m venv venv
source venv/bin/activate

# Gerekli Python paketlerini yükle
pip install -r requirements.txt
pip install gevent

# Nginx yapılandırmasını kopyala
sudo cp nginx.conf /etc/nginx/sites-available/tea-order
sudo ln -s /etc/nginx/sites-available/tea-order /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Systemd servis dosyasını kopyala
sudo cp tea-order.service /etc/systemd/system/

# Nginx'i yeniden başlat
sudo systemctl restart nginx

# SSL sertifikası al
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Servisi başlat ve otomatik başlatmayı etkinleştir
sudo systemctl daemon-reload
sudo systemctl start tea-order
sudo systemctl enable tea-order 