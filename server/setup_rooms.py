import os
import json
import hashlib
import random

# Veri dizini
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ROOMS_FILE = os.path.join(DATA_DIR, 'rooms.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# Veri dizini yoksa oluştur
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Şifre hash fonksiyonu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Oda adları
oda_adlari = [
    "Muhasebe",
    "İnsan Kaynakları",
    "Bilgi İşlem",
    "Pazarlama",
    "Satış"
]

# İsim listesi
isimler = [
    "Ahmet", "Mehmet", "Ayşe", "Fatma", "Mustafa", "Ali", "Zeynep", "Hüseyin", 
    "Emine", "İbrahim", "Hatice", "Hasan", "Meryem", "Ömer", "Elif", "Muhammed", 
    "Halil", "Şerife", "Hüseyin", "Havva", "İsmail", "Emine", "Osman", "Fadime",
    "Ramazan", "Hatice", "Yusuf", "Zeliha", "Bekir", "Hacer", "Murat", "Ayşe"
]

# Soyadlar
soyadlar = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım", "Öztürk",
    "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç",
    "Kurt", "Özkan", "Şimşek", "Polat", "Korkmaz", "Karaca", "Alp", "Altın",
    "Taş", "Aksoy", "Barış", "Tekin", "Bulut", "Yalçın", "Köse", "Aktaş"
]

# Odalar ve kullanıcılar oluştur
rooms = {}
users = {}

# Her oda için 4 rastgele kişi oluştur
for oda in oda_adlari:
    # Bu oda için 4 benzersiz kişi seç
    oda_kisileri = []
    used_indices = set()
    
    for _ in range(4):
        # Rastgele benzersiz isim ve soyad indeksi seç
        while True:
            isim_index = random.randint(0, len(isimler) - 1)
            soyad_index = random.randint(0, len(soyadlar) - 1)
            index_pair = (isim_index, soyad_index)
            
            if index_pair not in used_indices:
                used_indices.add(index_pair)
                break
        
        # Tam isim oluştur
        tam_isim = f"{isimler[isim_index]} {soyadlar[soyad_index]}"
        oda_kisileri.append(tam_isim)
        
        # Kullanıcı oluştur
        user_id = f"{oda}:{tam_isim}"
        users[user_id] = {
            "password": hash_password("123"),
            "first_login": True,
            "room": oda,
            "person": tam_isim
        }
    
    # Odayı ekle
    rooms[oda] = oda_kisileri

# JSON dosyalarına kaydet
with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
    json.dump(rooms, f, ensure_ascii=False, indent=4)

with open(USERS_FILE, 'w', encoding='utf-8') as f:
    json.dump(users, f, ensure_ascii=False, indent=4)

print(f"Odalar ve kullanıcılar başarıyla oluşturuldu.")
print(f"Toplam {len(rooms)} oda, {len(users)} kullanıcı oluşturuldu.")
print(f"Rooms dosyası: {ROOMS_FILE}")
print(f"Users dosyası: {USERS_FILE}") 