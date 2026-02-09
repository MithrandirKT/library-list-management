"""
Kitap Temalı İkon Oluşturucu
Windows shortcut'ları için kitap temalı ikonlar oluşturur
"""

import os
from PIL import Image, ImageDraw, ImageFont

def kitap_ikon_olustur(boyut=256, renk="#8B4513"):
    """Kütüphane temalı ikon oluşturur - Yan yana dikey kitaplar"""
    # Kütüphane temalı arka plan (açık bej/krem)
    arka_plan = "#F5E6D3"
    img = Image.new('RGBA', (boyut, boyut), arka_plan)
    draw = ImageDraw.Draw(img)
    
    # Kitapların renkleri (kütüphane temalı - farklı tonlar)
    kitap_renkleri = [
        "#8B4513",  # Koyu kahverengi
        "#A0522D",  # Sienna
        "#654321",  # Koyu kahverengi
        "#6B4423",  # Kahverengi
        "#7B3F00",  # Koyu kahverengi
    ]
    
    # Kitapların sayısı
    kitap_sayisi = 4
    
    # Her kitap için genişlik ve yükseklik
    kitap_genislik = int(boyut * 0.18)  # Her kitap genişliği
    kitap_yukseklik = int(boyut * 0.65)  # Kitap yüksekliği (dikey)
    kitaplar_arasi_bosluk = int(boyut * 0.02)  # Kitaplar arası boşluk
    
    # Tüm kitapların toplam genişliği
    toplam_genislik = (kitap_genislik * kitap_sayisi) + (kitaplar_arasi_bosluk * (kitap_sayisi - 1))
    
    # Başlangıç x pozisyonu (ortalamak için)
    baslangic_x = (boyut - toplam_genislik) // 2
    baslangic_y = int(boyut * 0.15)  # Üstten boşluk
    
    # Her kitabı çiz
    for i in range(kitap_sayisi):
        kitap_x = baslangic_x + (i * (kitap_genislik + kitaplar_arasi_bosluk))
        kitap_y = baslangic_y
        
        # Kitap rengi (farklı tonlar)
        kitap_rengi = kitap_renkleri[i % len(kitap_renkleri)]
        
        # Ana kitap gövdesi (dikey dikdörtgen)
        draw.rectangle(
            [kitap_x, kitap_y, kitap_x + kitap_genislik, kitap_y + kitap_yukseklik],
            fill=kitap_rengi,
            outline="#4A2C1A",  # Koyu kenarlık
            width=2
        )
        
        # Kitap cilt çizgisi (dikey - sol tarafta)
        cilt_x = kitap_x + int(kitap_genislik * 0.15)
        draw.line(
            [cilt_x, kitap_y, cilt_x, kitap_y + kitap_yukseklik],
            fill="#4A2C1A",
            width=2
        )
        
        # Kitap sayfaları (yatay çizgiler - sayfa kenarları)
        sayfa_rengi = "#F5E6D3"
        sayfa_sayisi = 5
        for j in range(sayfa_sayisi):
            sayfa_y = kitap_y + int(kitap_yukseklik * 0.15) + (j * int(kitap_yukseklik * 0.12))
            # Sol sayfa kenarı
            draw.line(
                [kitap_x + int(kitap_genislik * 0.2), sayfa_y,
                 kitap_x + int(kitap_genislik * 0.5), sayfa_y],
                fill=sayfa_rengi,
                width=1
            )
            # Sağ sayfa kenarı
            draw.line(
                [kitap_x + int(kitap_genislik * 0.5), sayfa_y,
                 kitap_x + int(kitap_genislik * 0.85), sayfa_y],
                fill=sayfa_rengi,
                width=1
            )
        
        # Kitap üzerinde dekoratif çizgiler (cilt detayları)
        for j in range(2):
            dekor_y = kitap_y + int(kitap_yukseklik * 0.25) + (j * int(kitap_yukseklik * 0.3))
            draw.line(
                [kitap_x + int(kitap_genislik * 0.25), dekor_y,
                 kitap_x + int(kitap_genislik * 0.75), dekor_y],
                fill="#6B4423",
                width=1
            )
        
        # Kitap gölgesi (alt kısımda)
        gölge_y = kitap_y + kitap_yukseklik
        draw.ellipse(
            [kitap_x - 2, gölge_y, kitap_x + kitap_genislik + 2, gölge_y + int(boyut * 0.05)],
            fill="#D2B48C",
            outline=None
        )
    
    # Duvara dayanmış görünümü için alt kısımda çizgi (zemin)
    zemin_y = baslangic_y + kitap_yukseklik + int(boyut * 0.03)
    draw.line(
        [int(boyut * 0.1), zemin_y, int(boyut * 0.9), zemin_y],
        fill="#8B7355",
        width=3
    )
    
    return img

def ikon_kaydet():
    """İkon dosyasını kaydeder"""
    import os
    
    # Eski ikon dosyalarını sil
    if os.path.exists('kitap_ikon.png'):
        os.remove('kitap_ikon.png')
    if os.path.exists('kitap_ikon.ico'):
        os.remove('kitap_ikon.ico')
    
    # Ana ikon (256x256) - Windows shortcut'ları için yeterli
    print("🎨 Yeni kütüphane temalı ikon oluşturuluyor...")
    ana_ikon = kitap_ikon_olustur(256)
    
    # PNG olarak kaydet (Windows shortcut'ları PNG'yi de destekler)
    ana_ikon.save('kitap_ikon.png', format='PNG')
    print("✅ PNG ikon oluşturuldu: kitap_ikon.png")
    
    # ICO dosyası oluştur (Windows için daha iyi destek)
    # Farklı boyutlarda ICO oluştur
    try:
        # RGB moduna çevir (ICO için gerekli)
        ico_ikon = ana_ikon.convert('RGB')
        # ICO olarak kaydet
        ico_ikon.save('kitap_ikon.ico', format='ICO')
        print("✅ ICO ikon oluşturuldu: kitap_ikon.ico")
        print("💡 İkon dosyaları başarıyla oluşturuldu!")
    except Exception as e:
        print(f"⚠️ ICO kaydedilemedi (PNG kullanılacak): {e}")
        print("💡 PNG dosyası Windows shortcut'larında da çalışır.")

if __name__ == "__main__":
    try:
        ikon_kaydet()
        print("\n✅ İkon başarıyla oluşturuldu!")
    except ImportError:
        print("❌ Hata: PIL (Pillow) kütüphanesi gerekli!")
        print("Kurulum için: pip install Pillow")
    except Exception as e:
        print(f"❌ Hata: {e}")
