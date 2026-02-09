"""
API Key Yönetimi Modülü
Groq API key yükleme, kaydetme ve yönetim işlemleri
"""

import os
from typing import Optional


class APIKeyManager:
    """API key yönetimi için sınıf"""
    
    def __init__(self, api_key_dosyasi: str = "groq_api_key.txt"):
        """
        Args:
            api_key_dosyasi: API key dosyası yolu
        """
        self.api_key_dosyasi = api_key_dosyasi
        self.api_key: Optional[str] = None
    
    def yukle(self) -> Optional[str]:
        """
        API key'i dosyadan yükler
        
        Returns:
            API key veya None
        """
        try:
            if os.path.exists(self.api_key_dosyasi):
                with open(self.api_key_dosyasi, 'r', encoding='utf-8') as f:
                    key = f.read().strip()
                    if key:
                        print(f"API key dosyadan yüklendi: {key[:10]}...")
                        self.api_key = key
                        return key
                    else:
                        print("API key dosyası boş!")
            else:
                print(f"API key dosyası bulunamadı: {self.api_key_dosyasi}")
        except Exception as e:
            print(f"Groq API key yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
        
        self.api_key = None
        return None
    
    def kaydet(self, api_key: str) -> bool:
        """
        API key'i dosyaya kaydeder
        
        Args:
            api_key: Kaydedilecek API key
            
        Returns:
            Başarılı ise True
        """
        try:
            api_key_clean = api_key.strip()
            with open(self.api_key_dosyasi, 'w', encoding='utf-8') as f:
                f.write(api_key_clean)
            self.api_key = api_key_clean
            print(f"API key kaydedildi: {api_key_clean[:10]}...")
            print(f"Dosya yolu: {os.path.abspath(self.api_key_dosyasi)}")
            return True
        except Exception as e:
            print(f"API key kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def sil(self) -> bool:
        """
        API key'i siler
        
        Returns:
            Başarılı ise True
        """
        try:
            if os.path.exists(self.api_key_dosyasi):
                os.remove(self.api_key_dosyasi)
            self.api_key = None
            print("API key silindi.")
            return True
        except Exception as e:
            print(f"API key silme hatası: {e}")
            return False
    
    def durum(self) -> str:
        """
        API key durumunu döndürür
        
        Returns:
            "✓" veya "✗"
        """
        if self.api_key:
            return "✓"
        return "✗"
    
    def get(self) -> Optional[str]:
        """
        Mevcut API key'i döndürür
        
        Returns:
            API key veya None
        """
        return self.api_key
