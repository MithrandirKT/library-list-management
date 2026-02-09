"""
Mevcut kitap_listesi.xlsx dosyasını yeni formata göre günceller
"""

import pandas as pd
import os

def excel_formatini_guncelle():
    """Mevcut Excel dosyasını yeni formata göre güncelle"""
    dosya_adi = "Kutuphanem.xlsx"
    
    if not os.path.exists(dosya_adi):
        print(f"'{dosya_adi}' dosyası bulunamadı!")
        return
    
    try:
        # Mevcut dosyayı oku
        df = pd.read_excel(dosya_adi, engine='openpyxl')
        
        print(f"Mevcut dosya yüklendi. Toplam {len(df)} satır bulundu.")
        
        # Yeni sütun sırası
        yeni_sutun_sirasi = [
            "Kitap Adı",
            "Yazar",
            "Orijinal Adı", 
            "Tür",
            "Ülke/Edebi Gelenek",
            "Çıkış Yılı",
            "Anlatı Yılı",
            "Konusu",
            "Not"
        ]
        
        # Eksik sütunları ekle
        for sutun in yeni_sutun_sirasi:
            if sutun not in df.columns:
                df[sutun] = ""
                print(f"Eksik sütun eklendi: {sutun}")
        
        # Sütun sırasını düzenle
        df = df[yeni_sutun_sirasi]
        
        # Yedek oluştur
        yedek_dosya = "kitap_listesi_yedek.xlsx"
        if os.path.exists(yedek_dosya):
            os.remove(yedek_dosya)
        pd.read_excel(dosya_adi, engine='openpyxl').to_excel(yedek_dosya, index=False, engine='openpyxl')
        print(f"Yedek oluşturuldu: {yedek_dosya}")
        
        # Yeni formata göre kaydet
        df.to_excel(dosya_adi, index=False, engine='openpyxl')
        
        print(f"\nBaşarılı! '{dosya_adi}' dosyası yeni formata göre güncellendi.")
        print(f"\nYeni sütun sırası:")
        for i, sutun in enumerate(yeni_sutun_sirasi, 1):
            print(f"  {i}. {sutun}")
        
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("Excel Format Güncelleme")
    print("=" * 50)
    print()
    excel_formatini_guncelle()
    print()
    input("Devam etmek için Enter'a basın...")
