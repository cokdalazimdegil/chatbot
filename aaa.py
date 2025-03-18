import requests
import json
import speech_recognition as sr
import pyttsx3
import os
import pygame
import smtplib
import re
import unicodedata
import random
import threading
import time
import datetime
import feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AsenaAssistant:
    def __init__(self):
        # Initialize memory structure
        self.memory = {
            "messages": [], 
            "contacts": {},
            "user_info": {},
            "short_term_memory": [],
            "long_term_memory": []
        }
        
        # Load saved memory if exists
        self.load_memory()
        
        # Initialize speech components
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        
        # Config variables
        self.chat_mode = None
        self.API_KEY = "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"  # API anahtarını değiştir
        self.music_playing = False
        self.music_folder = "music"  # Müzik dosyalarının bulunduğu klasör
        self.news_url = "https://nitter.poast.org/pusholder/rss"
        
        # State variables
        self.is_sleeping = False
        self.last_interaction_time = time.time()
        self.last_self_talk_time = time.time()
        self.self_talk_interval = 600  # 10 dakika
        self.sleep_timeout = 60  # 1 dakika
        
        # Karşılama mesajları
        self.greetings = [
            "Merhaba! Asena hizmetinizde. Bugün size nasıl yardımcı olabilirim?",
            "Selam! Ben Asena. Nasılsın bugün?",
            "Günaydın! Asena burada. Seni görmek güzel.",
            "Hoş geldin! Asena'yı çalıştırdın. Nasıl yardımcı olabilirim?",
            "Merhaba! Asena aktif. Bugün ne yapmak istersin?",
            "Hey! Asena seninle. Nasıl bir gün geçiriyorsun?",
            "İyi günler! Asena dinliyor. Bugün planın ne?",
            "Selam! Asena hazır. Bugün sana nasıl destek olabilirim?",
            "Merhaba! Asena yardıma hazır. Ne yapabilirim senin için?",
            "Hoş geldin! Asena yanında. Bugün ne konuşmak istersin?"
        ]
        
        # Müzik klasörünü oluştur
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            
        # Thread'leri başlat
        self.setup_threads()
        
        # Mixer'ı başlat
        pygame.mixer.init()
    
    def setup_threads(self):
        """Thread'leri başlatır"""
        # Uyku modu ve kendi kendine konuşma thread'i
        self.state_thread = threading.Thread(target=self.monitor_state, daemon=True)
        self.state_thread.start()
        
        # Hotword detection thread'i
        if self.chat_mode == "sesli":
            self.hotword_thread = threading.Thread(target=self.hotword_detection, daemon=True)
            self.hotword_thread.start()
    
    def speak(self, text):
        """Metni sesli olarak okur"""
        # Emoji'leri temizle - sadece metni konuşma için kullan
        clean_text = self.remove_emojis(text)
        print("Asena:", text)  # Terminalde emoji dahil tam metni göster
        
        # Konuşma sırasında son etkileşim zamanını güncelle
        self.last_interaction_time = time.time()
        
        if self.is_sleeping:
            self.is_sleeping = False
            print("Asena uyandı.")
        
        self.engine.say(clean_text)  # Sesli olarak emoji olmadan oku
        self.engine.runAndWait()
    
    def remove_emojis(self, text):
        """Metinden emoji karakterlerini temizler"""
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F700-\U0001F77F"  # alchemical symbols
                                   u"\U0001F780-\U0001F7FF"  # Geometric Shapes
                                   u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                                   u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                                   u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                                   u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                                   u"\U00002702-\U000027B0"  # Dingbats
                                   u"\U000024C2-\U0001F251" 
                                   "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    def listen(self):
        """Mikrofon dinleme"""
        # Etkileşim zamanını güncelle
        self.last_interaction_time = time.time()
        
        # Uyku modundan çık
        if self.is_sleeping:
            self.is_sleeping = False
            print("Asena uyandı.")
        
        with sr.Microphone() as source:
            print("Asena dinliyor...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        
        try:
            text = self.recognizer.recognize_google(audio, language="tr-TR")
            print("Sen (Sesli):", text)
            return text
        except sr.UnknownValueError:
            if not self.is_sleeping:
                self.speak("Seni anlayamadım, tekrar eder misin?")
            return ""
        except sr.RequestError:
            if not self.is_sleeping:
                self.speak("Ses tanıma servisine ulaşılamıyor.")
            return ""
    
    def hotword_detection(self):
        """Arka planda sürekli çalışan bir thread ile "asena" kelimesini dinler"""
        while True:
            if self.is_sleeping and self.chat_mode == "sesli":
                try:
                    with sr.Microphone() as source:
                        print("Hotword bekleniyor... ('asena' deyin)")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=2)
                    
                    try:
                        text = self.recognizer.recognize_google(audio, language="tr-TR").lower()
                        if "asena" in text:
                            self.is_sleeping = False
                            self.speak("Evet, buradayım. Nasıl yardımcı olabilirim?")
                    except sr.UnknownValueError:
                        pass  # Sessiz
                    except sr.RequestError:
                        pass  # Sessiz
                except Exception as e:
                    print(f"Hotword dinleme hatası: {e}")
                    time.sleep(1)
            time.sleep(0.1)  # CPU yükünü azaltmak için kısa bir bekleme
    
    def monitor_state(self):
        """Asistan durumunu izler, uyku moduna geçiş yapar ve kendi kendine konuşur"""
        while True:
            current_time = time.time()
            
            # Uyku modunu kontrol et
            if not self.is_sleeping and (current_time - self.last_interaction_time > self.sleep_timeout):
                self.is_sleeping = True
                print("Asena uyku moduna geçti. 'Asena' diyerek uyandırabilirsiniz.")
            
            # Kendi kendine konuşma
            if not self.is_sleeping and (current_time - self.last_self_talk_time > self.self_talk_interval):
                self.self_talk()
                self.last_self_talk_time = current_time
            
            time.sleep(1)  # CPU yükünü azaltmak için
    
    def self_talk(self):
        """Asistan kendi kendine konuşma yapar"""
        talk_type = random.choice(["hava", "saat", "haber"])
        
        if talk_type == "hava":
            self.speak("Bugün hava güzel görünüyor. Umarım keyifli bir gün geçiriyorsunuz.")
        elif talk_type == "saat":
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.speak(f"Şu anda saat {current_time}. Zamanınızı verimli kullanmanızı dilerim.")
        elif talk_type == "haber":
            self.read_news()
    
    def read_news(self):
        """RSS'den haber okur"""
        try:
            feed = feedparser.parse(self.news_url)
            if feed.entries:
                self.speak("Güncel haberlerden bazıları:")
                for i, entry in enumerate(feed.entries[:3]):  # Son 3 haberi al
                    self.speak(f"{i+1}. {entry.title}")
            else:
                self.speak("Şu anda haberlere erişemiyorum.")
        except Exception as e:
            self.speak("Haberleri okurken bir sorun oluştu.")
            print(f"Haber okuma hatası: {e}")
    
    def load_memory(self):
        """Kaydedilmiş belleği yükler"""
        if os.path.exists("asena_memory.json"):
            try:
                with open("asena_memory.json", "r", encoding="utf-8") as file:
                    loaded_memory = json.load(file)
                    
                    # Eksik anahtarları kontrol et ve ekle
                    for key in ["messages", "contacts", "user_info", "short_term_memory", "long_term_memory"]:
                        if key not in loaded_memory:
                            loaded_memory[key] = []
                            if key in ["user_info", "contacts"]:
                                loaded_memory[key] = {}
                    
                    self.memory = loaded_memory
            except Exception as e:
                print(f"Bellek yükleme hatası: {e}")
                # Bellek dosyasını yedekle ve yeni bir bellek oluştur
                if os.path.exists("asena_memory.json"):
                    os.rename("asena_memory.json", f"asena_memory_backup_{int(time.time())}.json")
    
    def save_memory(self):
        """Belleği dosyaya kaydeder"""
        with open("asena_memory.json", "w", encoding="utf-8") as file:
            json.dump(self.memory, file, ensure_ascii=False, indent=4)
    
    def extract_user_info(self, text):
        """Kullanıcıdan önemli bilgileri çıkarır ve bellekte saklar"""
        
        # İsim tanıma
        name_patterns = [
            r"(benim adım|ismim) ([A-Za-zÇçĞğİıÖöŞşÜü]+)",
            r"(ben) ([A-Za-zÇçĞğİıÖöŞşÜü]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(2)
                if "name" not in self.memory["user_info"] or self.memory["user_info"]["name"] != name:
                    self.memory["user_info"]["name"] = name
                    self.add_to_short_term_memory(f"Kullanıcının adı: {name}")
                    self.add_to_long_term_memory(f"Kullanıcının adı: {name}")
        
        # Yaş tanıma
        age_patterns = [
            r"(yaşım|ben) (\d+) yaşında(yım)?",
            r"(\d+) yaşında(yım)?"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = match.group(2)
                if "age" not in self.memory["user_info"] or self.memory["user_info"]["age"] != age:
                    self.memory["user_info"]["age"] = age
                    self.add_to_short_term_memory(f"Kullanıcının yaşı: {age}")
                    self.add_to_long_term_memory(f"Kullanıcının yaşı: {age}")
        
        # İş tanıma
        job_patterns = [
            r"(ben bir|işim|mesleğim) ([A-Za-zÇçĞğİıÖöŞşÜü]+)",
            r"(ben) ([A-Za-zÇçĞğİıÖöŞşÜü]+) (olarak çalışıyorum)"
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                job = match.group(2)
                if "job" not in self.memory["user_info"] or self.memory["user_info"]["job"] != job:
                    self.memory["user_info"]["job"] = job
                    self.add_to_short_term_memory(f"Kullanıcının mesleği: {job}")
                    self.add_to_long_term_memory(f"Kullanıcının mesleği: {job}")
        
        # Tercihler
        like_pattern = r"(ben|benim) ([A-Za-zÇçĞğİıÖöŞşÜü]+) (sev|beğen)"
        match = re.search(like_pattern, text, re.IGNORECASE)
        if match:
            liked_thing = match.group(2)
            if "likes" not in self.memory["user_info"]:
                self.memory["user_info"]["likes"] = []
            if liked_thing not in self.memory["user_info"]["likes"]:
                self.memory["user_info"]["likes"].append(liked_thing)
                self.add_to_short_term_memory(f"Kullanıcı {liked_thing} seviyor")
                self.add_to_long_term_memory(f"Kullanıcı {liked_thing} seviyor")
        
        # Hoşlanmadıkları
        dislike_pattern = r"(ben|benim) ([A-Za-zÇçĞğİıÖöŞşÜü]+) (sevmiyorum|hoşlanmıyorum)"
        match = re.search(dislike_pattern, text, re.IGNORECASE)
        if match:
            disliked_thing = match.group(2)
            if "dislikes" not in self.memory["user_info"]:
                self.memory["user_info"]["dislikes"] = []
            if disliked_thing not in self.memory["user_info"]["dislikes"]:
                self.memory["user_info"]["dislikes"].append(disliked_thing)
                self.add_to_short_term_memory(f"Kullanıcı {disliked_thing} sevmiyor")
                self.add_to_long_term_memory(f"Kullanıcı {disliked_thing} sevmiyor")
                
        self.save_memory()
    
    def add_to_short_term_memory(self, info):
        """Kısa süreli belleğe bilgi ekler (son 20 bilgi)"""
        if "short_term_memory" not in self.memory:
            self.memory["short_term_memory"] = []
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.memory["short_term_memory"].append({"info": info, "timestamp": timestamp})
        # Kısa süreli belleği 20 girişle sınırla
        if len(self.memory["short_term_memory"]) > 20:
            self.memory["short_term_memory"].pop(0)  # En eski girişi sil
    
    def add_to_long_term_memory(self, info):
        """Uzun süreli belleğe bilgi ekler"""
        if "long_term_memory" not in self.memory:
            self.memory["long_term_memory"] = []
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Aynı bilginin zaten var olup olmadığını kontrol et
        for entry in self.memory["long_term_memory"]:
            if entry["info"] == info:
                entry["timestamp"] = timestamp  # Varsa zaman damgasını güncelle
                return
        # Yoksa yeni ekle
        self.memory["long_term_memory"].append({"info": info, "timestamp": timestamp})
    
    def get_memory_context(self):
        """Kullanıcı bilgilerini ve kısa süreli hafızayı içeren bağlam metni oluşturur"""
        context = "Kullanıcı hakkında bilgiler:\n"
        
        # Kullanıcı bilgilerini ekle
        if "user_info" in self.memory and self.memory["user_info"]:
            for key, value in self.memory["user_info"].items():
                if key == "name":
                    context += f"- İsim: {value}\n"
                elif key == "age":
                    context += f"- Yaş: {value}\n"
                elif key == "job":
                    context += f"- Meslek: {value}\n"
                elif key == "likes" and value:
                    context += f"- Sevdikleri: {', '.join(value)}\n"
                elif key == "dislikes" and value:
                    context += f"- Sevmedikleri: {', '.join(value)}\n"
        
        # Kısa süreli hafızadan son 5 giriş
        context += "\nSon konuşmalardan bilgiler:\n"
        if "short_term_memory" in self.memory and self.memory["short_term_memory"]:
            recent_memories = self.memory["short_term_memory"][-5:]
            for memory in recent_memories:
                context += f"- {memory['info']}\n"
        
        return context
    
    def chat_with_asena(self, user_input):
        """Asena ile sohbet eder"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yourwebsite.com",  # Kendi site URL'ni ekle
            "X-Title": "Asena Assistant"
        }
        
        # Kullanıcı girdisinden bilgi çıkar
        self.extract_user_info(user_input)
        
        # Konuşma bağlamını oluştur
        context = self.get_memory_context()
        
        # Sistem mesajını kullanıcı bilgileri ile zenginleştir
        system_message = {
            "role": "system", 
            "content": f"Sen Asena, Türkçe konuşan bir kişisel asistansın. Kullanıcı hakkında şunları biliyorsun:\n{context}"
        }
        
        # Eğer sistem mesajı yoksa ekle
        if not any(msg.get("role") == "system" for msg in self.memory["messages"]):
            self.memory["messages"].insert(0, system_message)
        else:
            # Sistem mesajını güncelle
            for idx, msg in enumerate(self.memory["messages"]):
                if msg.get("role") == "system":
                    self.memory["messages"][idx] = system_message
                    break
        
        # Kullanıcı mesajını ekle
        self.memory["messages"].append({"role": "user", "content": user_input})
        
        # Mesaj geçmişini son 10 mesajla sınırla (sistem mesajı dışında)
        if len(self.memory["messages"]) > 11:  # 1 sistem mesajı + 10 konuşma mesajı
            # Sistem mesajını koru
            system_msg = next((msg for msg in self.memory["messages"] if msg.get("role") == "system"), None)
            # Diğer mesajları filtrele ve son 10'u al
            other_msgs = [msg for msg in self.memory["messages"] if msg.get("role") != "system"][-10:]
            # Yeni mesaj listesini oluştur
            self.memory["messages"] = [system_msg] + other_msgs if system_msg else other_msgs
        
        data = {
            "model": "google/gemma-3-12b-it:free",
            "messages": self.memory["messages"]
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                self.speak(reply)
                
                self.memory["messages"].append({"role": "assistant", "content": reply})
                self.save_memory()
            else:
                self.speak(f"Bir hata oluştu. Hata kodu: {response.status_code}")
        except Exception as e:
            self.speak(f"Bağlantı hatası: {e}")
    
    def play_music(self, song_name=None):
        """Müzik çalar"""
        music_files = [f for f in os.listdir(self.music_folder) if f.endswith(('.mp3', '.wav'))]
        
        if not music_files:
            self.speak("Müzik klasöründe hiç şarkı bulunamadı. Lütfen 'music' klasörüne mp3 veya wav dosyaları ekleyin.")
            return
        
        if pygame.mixer.music.get_busy() and self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False
            self.speak("Müzik durduruldu.")
            return
        
        if song_name:
            found = False
            for file in music_files:
                if song_name.lower() in file.lower():
                    song_path = os.path.join(self.music_folder, file)
                    found = True
                    break
            if not found:
                self.speak(f"{song_name} adlı şarkı bulunamadı.")
                return
        else:
            song_path = os.path.join(self.music_folder, music_files[0])
        
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            self.music_playing = True
            self.speak(f"Çalınan şarkı: {os.path.basename(song_path)}")
        except Exception as e:
            self.speak(f"Müzik çalınırken bir hata oluştu: {e}")
    
    def stop_music(self):
        """Müziği durdurur"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            self.music_playing = False
            self.speak("Müzik durduruldu.")
        else:
            self.speak("Şu anda çalan müzik yok.")
    
    def send_message(self, contact_name, message):
        """Kayıtlı kişiye mesaj gönderir"""
        if "contacts" not in self.memory:
            self.memory["contacts"] = {}
            self.save_memory()
        
        if contact_name.lower() not in self.memory["contacts"]:
            self.speak(f"{contact_name} adlı kişi kayıtlı değil. Lütfen önce kişiyi kaydedin.")
            return
        
        contact = self.memory["contacts"][contact_name.lower()]
        
        try:
            # E-posta gönderme ayarları
            sender_email = "your_email@gmail.com"  # Kendi e-posta adresinizi girin
            sender_password = "your_password"  # Kendi şifrenizi girin
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = contact["email"]
            msg['Subject'] = "Asena'dan Mesaj"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, contact["email"], text)
            server.quit()
            
            self.speak(f"Mesaj {contact_name}'a gönderildi.")
        except Exception as e:
            self.speak(f"Mesaj gönderirken bir hata oluştu: {e}")
    
    def add_contact(self, name, email, phone=None):
        """Kişi ekler"""
        if "contacts" not in self.memory:
            self.memory["contacts"] = {}
        
        self.memory["contacts"][name.lower()] = {
            "name": name,
            "email": email,
            "phone": phone
        }
        self.save_memory()
        self.speak(f"{name} kişisi başarıyla kaydedildi.")
    
    def process_command(self, command):
        """Komut işleme"""
        command = command.lower()
        
        # Asena hotword'ü
        if command == "asena" and self.is_sleeping:
            self.is_sleeping = False
            self.speak("Evet, buradayım. Nasıl yardımcı olabilirim?")
            return True
        
        # Müzik komutları
        if "müzik çal" in command or "şarkı çal" in command:
            song_name = None
            if "çal" in command:
                song_name = command.split("çal", 1)[1].strip()
            self.play_music(song_name)
            return True
        
        elif "müziği durdur" in command or "şarkıyı durdur" in command or "müzik kapat" in command:
            self.stop_music()
            return True
        
        # Mesaj gönderme komutları
        elif "mesaj gönder" in command or "mesaj at" in command:
            parts = command.split("mesaj", 1)[1].strip()
            if "gönder" in parts:
                parts = parts.split("gönder", 1)[1].strip()
            elif "at" in parts:
                parts = parts.split("at", 1)[1].strip()
                
            try:
                contact_name, message = parts.split("diyor ki", 1)
                contact_name = contact_name.strip()
                message = message.strip()
                self.send_message(contact_name, message)
            except ValueError:
                self.speak("Mesaj gönderme formatı anlaşılamadı. Lütfen 'Ahmet'e mesaj gönder diyor ki merhaba' şeklinde söyleyin.")
            return True
        
        # Kişi ekleme komutları
        elif "kişi ekle" in command or "kişi kaydet" in command:
            try:
                parts = command.split("ekle", 1)[1].strip() if "ekle" in command else command.split("kaydet", 1)[1].strip()
                name, email = parts.split("email", 1)
                name = name.strip()
                email = email.strip()
                self.add_contact(name, email)
            except ValueError:
                self.speak("Kişi ekleme formatı anlaşılamadı. Lütfen 'kişi ekle Ahmet email ahmet@example.com' şeklinde söyleyin.")
            return True
        
        # Haber okuma komutu
        elif "haber oku" in command or "haberleri oku" in command:
            self.read_news()
            return True
        
        # Bellek sorguları
        elif "beni hatırlıyor musun" in command or "benim adım ne" in command:
            if "user_info" in self.memory and "name" in self.memory["user_info"]:
                self.speak(f"Evet, adınız {self.memory['user_info']['name']}.")
            else:
                self.speak("Henüz adınızı bilmiyorum. Bana adınızı söyleyebilirsiniz.")
            return True
        
        elif "ben kimim" in command:
            if "user_info" in self.memory and self.memory["user_info"]:
                info = self.memory["user_info"]
                response = "Benim bildiğim kadarıyla, "
                if "name" in info:
                    response += f"adınız {info['name']}, "
                if "age" in info:
                    response += f"{info['age']} yaşındasınız, "
                if "job" in info:
                    response += f"mesleğiniz {info['job']}, "
                if "likes" in info and info["likes"]:
                    response += f"{', '.join(info['likes'])} seviyorsunuz, "
                if "dislikes" in info and info["dislikes"]:
                    response += f"{', '.join(info['dislikes'])} sevmiyorsunuz, "
                
                
                response = response.rstrip(", ") + "."
                self.speak(response)
            else:
                self.speak("Henüz sizinle ilgili yeterli bilgiye sahip değilim. Konuşmamız ilerledikçe sizi daha iyi tanıyacağım.")
            return True
            
        return False
    
    def run(self):
        self.speak("Merhaba! Ben Asena. Size nasıl yardımcı olabilirim?")
        
        # Sadece başlangıçta sohbet modunu sor
        while not self.chat_mode:
            mode = input("Sohbet modu seçin (yazılı/sesli): ").strip().lower()
            if mode in ["yazılı", "sesli"]:
                self.chat_mode = mode
                self.speak(f"{mode.capitalize()} mod seçildi.")
            else:
                self.speak("Lütfen geçerli bir mod seçin: yazılı veya sesli")
        
        while True:
            try:
                if self.chat_mode == "sesli":
                    user_input = self.listen()
                else:
                    user_input = input("Sen (Yazılı): ")
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["çık", "kapat", "görüşürüz"]:
                    self.speak("Görüşmek üzere!")
                    break
                    
                # Özel komutları kontrol et
                if not self.process_command(user_input):
                    # Eğer özel komut değilse normal sohbet et
                    self.chat_with_asena(user_input)
                    
            except KeyboardInterrupt:
                self.speak("Görüşmek üzere!")
                break
            except Exception as e:
                self.speak(f"Bir hata oluştu: {e}")
                continue

if __name__ == "__main__":
    asena = AsenaAssistant()
    asena.run()
