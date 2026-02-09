"""Constants for HasWave Deprem integration."""

DOMAIN = "haswave_deprem"

# KOERI kaynağı
KOERI_URL = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"

# Varsayılanlar
DEFAULT_UPDATE_INTERVAL = 300  # 5 dakika (saniye)
DEFAULT_MIN_MAGNITUDE = 0.0
DEFAULT_LIMIT = 50
DEFAULT_NOTIFY_ABOVE_MAGNITUDE = 4.0  # Bu büyüklük ve üzeri yeni depremde bildirim

# Config keys
CONF_UPDATE_INTERVAL = "update_interval"
CONF_MIN_MAGNITUDE = "min_magnitude"
CONF_LIMIT = "limit"
CONF_NOTIFY_ABOVE_MAGNITUDE = "notify_above_magnitude"
CONF_ALL_EARTHQUAKES = "all_earthquakes"
CONF_CITY = "city"
CONF_REGION = "region"

# Türkiye illeri (PHP ile uyumlu)
CITIES = [
    "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AKSARAY", "AMASYA", "ANKARA", "ANTALYA",
    "ARDAHAN", "ARTVİN", "AYDIN", "BALIKESİR", "BARTIN", "BATMAN", "BAYBURT", "BİLECİK",
    "BİNGÖL", "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI", "ÇORUM",
    "DENİZLİ", "DİYARBAKIR", "DÜZCE", "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM", "ESKİŞEHİR",
    "GAZİANTEP", "GİRESUN", "GÜMÜŞHANE", "HAKKARİ", "HATAY", "IĞDIR", "ISPARTA", "İSTANBUL",
    "İZMİR", "KAHRAMANMARAŞ", "KARABÜK", "KARAMAN", "KARS", "KASTAMONU", "KAYSERİ", "KİLİS",
    "KIRIKKALE", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ", "KONYA", "KÜTAHYA", "MALATYA", "MANİSA",
    "MARDİN", "MERSİN", "MUĞLA", "MUŞ", "NEVŞEHİR", "NİĞDE", "ORDU", "OSMANİYE", "RİZE",
    "SAKARYA", "SAMSUN", "SİİRT", "SİNOP", "SİVAS", "ŞANLIURFA", "ŞIRNAK", "TEKİRDAĞ",
    "TOKAT", "TRABZON", "TUNCELİ", "UŞAK", "VAN", "YALOVA", "YOZGAT", "ZONGULDAK",
]

# Bölgeler ve iller (PHP ile uyumlu)
REGIONS: dict[str, list[str]] = {
    "MARMARA": ["İSTANBUL", "BURSA", "KOCAELİ", "BALIKESİR", "SAKARYA", "TEKİRDAĞ", "ÇANAKKALE", "EDİRNE", "KIRKLARELİ", "YALOVA", "BİLECİK", "DÜZCE"],
    "EGE": ["İZMİR", "AYDIN", "MUĞLA", "MANİSA", "AFYONKARAHİSAR", "DENİZLİ", "KÜTAHYA", "UŞAK"],
    "AKDENİZ": ["ANTALYA", "ADANA", "MERSİN", "HATAY", "KAHRAMANMARAŞ", "OSMANİYE", "ISPARTA", "BURDUR"],
    "İÇ ANADOLU": ["ANKARA", "KONYA", "ESKİŞEHİR", "KAYSERİ", "SİVAS", "YOZGAT", "AKSARAY", "KIRIKKALE", "KIRŞEHİR", "NEVŞEHİR", "NİĞDE", "KARAMAN"],
    "KARADENİZ": ["SAMSUN", "TRABZON", "ORDU", "GİRESUN", "RİZE", "ZONGULDAK", "KARABÜK", "KASTAMONU", "SİNOP", "AMASYA", "TOKAT", "ÇORUM", "ARTVİN", "BARTIN", "BOLU", "DÜZCE"],
    "DOĞU ANADOLU": ["ERZURUM", "ERZİNCAN", "VAN", "MALATYA", "ELAZIĞ", "BİNGÖL", "MUŞ", "BİTLİS", "AĞRI", "KARS", "ARDAHAN", "IĞDIR", "TUNCELİ", "BAYBURT", "GÜMÜŞHANE"],
    "GÜNEYDOĞU ANADOLU": ["GAZİANTEP", "ŞANLIURFA", "DİYARBAKIR", "MARDİN", "BATMAN", "SİİRT", "ŞIRNAK", "HAKKARİ", "KİLİS", "ADIYAMAN"],
}
