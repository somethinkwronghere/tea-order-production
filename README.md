# Tea Order Production Setup

Bu proje, çay sipariş sisteminin production ortamına kurulumu için gerekli dosyaları içerir.

## Dosya Yapısı

```
tea-order-production/
├── server/                 # Ana uygulama kodu
├── nginx.conf             # Nginx yapılandırması
├── gunicorn_config.py     # Gunicorn yapılandırması
├── tea-order.service      # Systemd servis dosyası
├── setup.sh               # Kurulum scripti
└── requirements.txt       # Python bağımlılıkları
```

## Kurulum Adımları

1. DigitalOcean'da 1GB RAM, 25GB Disk, Ubuntu 22.04 LTS x64 droplet oluşturun
2. Domain'inizi DigitalOcean nameserver'larına yönlendirin
3. A kaydı oluşturun ve droplet IP'sini ekleyin
4. Projeyi droplet'e kopyalayın:
   ```bash
   scp -r /path/to/tea-order-production root@your_droplet_ip:/var/www/tea-order
   ```
5. Droplet'e SSH ile bağlanın:
   ```bash
   ssh root@your_droplet_ip
   ```
6. Kurulum scriptini çalıştırılabilir yapın:
   ```bash
   chmod +x setup.sh
   ```
7. Kurulumu başlatın:
   ```bash
   ./setup.sh
   ```

## Güvenlik Önlemleri

1. UFW firewall'u etkinleştirin:
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 22
   sudo ufw enable
   ```

## Monitoring ve Logging

Logları kontrol etmek için:
```bash
sudo journalctl -u tea-order -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Önemli Notlar

1. `nginx.conf` dosyasındaki `yourdomain.com` kısmını kendi domain'inizle değiştirin
2. `setup.sh` scriptindeki domain bilgilerini güncelleyin
3. Projenin tüm dosyalarının `www-data` kullanıcısına ait olduğundan emin olun
4. SSL sertifikası otomatik olarak yenilenecektir

## cPanel Entegrasyonu

1. cPanel'de domain'inizi yönetin
2. DNS ayarlarını DigitalOcean nameserver'larına yönlendirin
3. A kaydını droplet IP'sine yönlendirin 