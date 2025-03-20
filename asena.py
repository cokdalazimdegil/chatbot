import requests
import json
import speech_recognition as sr
import pyttsx3
import os
import pygame
import smtplib
import re
import random
import threading
import time
import datetime
import feedparser
import pytz
import keyboard
import psutil
import subprocess
import logging
import screen_brightness_control as sbc  # Ekran parlaklığı kontrolü
import comtypes.client  # Windows ses kontrolü
from phue import Bridge  # Philips Hue ışık kontrolü
import subprocess
import platform
import wmi  # Windows yönetim arabirimi
from colorama import Fore, Style
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart




class AsenaAssistant:

    
    def __init__(self):
        # Bellek dosyaları
        self.permanent_memory_file = "asena_permanent_memory.json"
        self.temporary_memory_file = "asena_temporary_memory.json"
        self.log_file = "asena_logs.txt"
        self.rules_file = "asena_rules.json"
        self.self_analysis_file = "asena_self_analysis.json"
        self.system_controller = SystemController()
        self.current_volume = 50
        self.current_brightness = 50
        
        # Loglama yapılandırması
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Bellek yapıları
        self.permanent_memory = {
            "user_info": {},
            "contacts": {},
            "reminders": [],
            "preferences": {},
            "system_commands": {},
            "self_awareness": {
                "creation_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "2.0",
                "capabilities": [
                    "Sesli komut tanıma",
                    "Metin tabanlı sohbet",
                    "Hatırlatıcılar",
                    "Hava durumu takibi",
                    "Sistem komutları",
                    "Müzik kontrolü",
                    "Öz farkındalık",
                    "Kendi kendine düşünme",
                    "Rapor hazırlama",
                    "Duygu analizi",
                    "Kullanıcı bilgisi öğrenme"
                ]
            }
        }
        
        self.temporary_memory = {
            "messages": [],
            "current_session": {
                "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "interactions": 0,
                "emotion_log": []
            },
            "short_term_memory": [],
            "thinking_log": []
        }
        
        # Karar motoru kuralları
        self.rules_engine = {
            "morning_greeting": {
                "condition": "self.get_hour() >= 5 and self.get_hour() < 12",
                "action": "self.speak('Günaydın! Bugün size nasıl yardımcı olabilirim?')"
            },
            "afternoon_greeting": {
                "condition": "self.get_hour() >= 12 and self.get_hour() < 18",
                "action": "self.speak('İyi günler! Size nasıl yardımcı olabilirim?')"
            },
            "evening_greeting": {
                "condition": "self.get_hour() >= 18 and self.get_hour() < 22",
                "action": "self.speak('İyi akşamlar! Size nasıl yardımcı olabilirim?')"
            },
            "night_greeting": {
                "condition": "self.get_hour() >= 22 or self.get_hour() < 5",
                "action": "self.speak('İyi geceler! Geç saatte size nasıl yardımcı olabilirim?')"
            },
            "weather_reminder": {
                "condition": "self.get_minute() == 0 and not self.is_sleeping",
                "action": "self.get_weather()"
            },
            "self_analysis": {
                "condition": "self.get_hour() % 3 == 0 and self.get_minute() == 0",
                "action": "self.perform_self_analysis()"
            },
            "reminder_check": {
                "condition": "self.get_minute() % 5 == 0",
                "action": "self.check_reminders()"
            },
            "long_silence": {
                "condition": "time.time() - self.last_interaction_time > 3600 and not self.is_sleeping",
                "action": "self.speak('Uzun süredir konuşmuyoruz. Ben hâlâ buradayım ve hazırım.')"
            }
        }
        
        # Öz farkındalık yapısı
        self.self_awareness = {
            "last_analysis": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "performance_metrics": {
                "successful_interactions": 0,
                "failed_interactions": 0,
                "command_success_rate": 0,
                "response_time_avg": 0,
                "total_interactions": 0
            },
            "mood": "normal",
            "memory_stats": {
                "permanent_memory_size": 0,
                "temporary_memory_size": 0,
                "short_term_items": 0
            },
            "system_stats": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "uptime": 0
            },
            "improvement_suggestions": []
        }
        
        # Bellek dosyalarını yükle
        self.load_memory()
        self.load_rules()
        
        # Ses bileşenlerini başlat
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()

        # Türkçe ses seçimi
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if hasattr(voice, 'languages') and 'turkish' in voice.languages:
                self.engine.setProperty('voice', voice.id)
                break
        
        # Config değişkenleri
        self.chat_mode = None
        self.API_KEY = "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"
        self.OPENWEATHER_API_KEY = "b8763f13f2f55b269179e33b07aca4aa"
        self.music_playing = False
        self.music_folder = "music"
        self.news_url = "https://feeds.bbci.co.uk/turkce/rss.xml"
        self.short_response = False
        
        # Durum değişkenleri
        self.is_sleeping = False
        self.last_interaction_time = time.time()
        self.last_self_talk_time = time.time()
        self.self_talk_interval = 900  # 15 dakika
        self.sleep_timeout = 60  # 1 dakika
        self.response_time_start = 0
        
        # Müzik klasörünü oluştur
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            
        # Pygame mixer'ı başlat
        pygame.mixer.init()
        
        logging.info("Asena başlatıldı")
        self.add_to_thinking_log("System", "Asena başlatıldı. Tüm sistemler hazır.")

        # Thread'leri başlat - run() yönteminde chat_mode belirlendikten sonra başlatılacak
        self.state_thread = None
        self.reminder_thread = None
        self.rules_thread = None
        self.self_awareness_thread = None
        self.hotword_thread = None



    def process_text(self, text):
        """Web arayüzünden gelen metni işle"""
        try:
            # Debugging için
            print(f"İşlenen metin: {text}")
            
            # Ses kontrolü
            if "ses" in text.lower():
                if "aç" in text.lower() or "artır" in text.lower():
                    self.current_volume = min(100, self.current_volume + 10)
                    return f"Ses seviyesi {self.current_volume} olarak ayarlandı"
                elif "kıs" in text.lower() or "azalt" in text.lower():
                    self.current_volume = max(0, self.current_volume - 10)
                    return f"Ses seviyesi {self.current_volume} olarak ayarlandı"
            
            # Parlaklık kontrolü
            elif "parlaklık" in text.lower():
                if "artır" in text.lower():
                    self.current_brightness = min(100, self.current_brightness + 10)
                    return f"Parlaklık {self.current_brightness} olarak ayarlandı"
                elif "azalt" in text.lower():
                    self.current_brightness = max(0, self.current_brightness - 10)
                    return f"Parlaklık {self.current_brightness} olarak ayarlandı"
            
            # Normal konuşma işleme
            response = self.normal_response(text)
            if response:
                return response
            
            return "Anlaşılamadı"
            
        except Exception as e:
            print(f"process_text hatası: {str(e)}")
            return f"Bir hata oluştu: {str(e)}"

    def normal_response(self, text):
        """Normal konuşma yanıtları"""
        text = text.lower()
        
        # Basit yanıtlar
        responses = {
            "merhaba": "Merhaba! Size nasıl yardımcı olabilirim?",
            "nasılsın": "İyiyim, teşekkür ederim. Siz nasılsınız?",
            "teşekkür": "Rica ederim!",
            "görüşürüz": "Görüşmek üzere!",
            "saat kaç": datetime.datetime.now().strftime("%H:%M"),
            "tarih": datetime.datetime.now().strftime("%d.%m.%Y")
        }
        
        for key in responses:
            if key in text:
                return responses[key]
        
        return None

    def get_volume(self):
        """Mevcut ses seviyesini döndür"""
        return self.current_volume
        
    def get_brightness(self):
        """Mevcut parlaklık seviyesini döndür"""
        return self.current_brightness

    

    def process_command(self, command):
        command = command.lower()
        
        # Ses kontrolü komutları
        if "ses" in command:
            if "aç" in command or "artır" in command or "yükselt" in command:
                self.system_controller.control_volume(action="up")
                self.speak("Ses seviyesi artırıldı.")
            elif "kıs" in command or "azalt" in command or "düşür" in command:
                self.system_controller.control_volume(action="down")
                self.speak("Ses seviyesi azaltıldı.")
            elif "kapat" in command or "sustur" in command:
                self.system_controller.control_volume(action="mute")
                self.speak("Ses kapatıldı.")
                
        # Parlaklık kontrolü komutları
        elif "parlaklık" in command or "ekran" in command:
            if "artır" in command or "yükselt" in command:
                self.system_controller.control_brightness(action="up")
                self.speak("Ekran parlaklığı artırıldı.")
            elif "azalt" in command or "düşür" in command:
                self.system_controller.control_brightness(action="down")
                self.speak("Ekran parlaklığı azaltıldı.")
            elif "ayarla" in command:
                # Sayısal değer varsa al
                try:
                    value = int(''.join(filter(str.isdigit, command)))
                    if 0 <= value <= 100:
                        self.system_controller.control_brightness(action="set", value=value)
                        self.speak(f"Ekran parlaklığı {value} olarak ayarlandı.")
                except ValueError:
                    self.speak("Geçerli bir parlaklık değeri belirtmediniz.")
                    
        # Işık kontrolü komutları
        elif "ışık" in command or "lamba" in command:
            room = "bedroom"  # Varsayılan oda
            if "yatak odası" in command:
                room = "bedroom"
            elif "salon" in command:
                room = "living"
            elif "mutfak" in command:
                room = "kitchen"
                
            if "aç" in command or "yak" in command:
                self.system_controller.control_room_lights(action="on", room=room)
                self.speak(f"{room} ışıkları açıldı.")
            elif "kapat" in command or "söndür" in command:
                self.system_controller.control_room_lights(action="off", room=room)
                self.speak(f"{room} ışıkları kapatıldı.")
            elif "ayarla" in command:
                try:
                    value = int(''.join(filter(str.isdigit, command)))
                    if 0 <= value <= 100:
                        self.system_controller.control_room_lights(action="set", 
                                                                room=room, 
                                                                value=value)
                        self.speak(f"{room} ışık seviyesi {value} olarak ayarlandı.")
                except ValueError:
                    self.speak("Geçerli bir ışık seviyesi belirtmediniz.")
        

    def load_memory(self):
        """Bellek dosyalarını yükler"""
        # Permanent memory yükleme
        if os.path.exists(self.permanent_memory_file):
            try:
                with open(self.permanent_memory_file, "r", encoding="utf-8") as file:
                    self.permanent_memory = json.load(file)
                logging.info("Kalıcı bellek başarıyla yüklendi.")
            except Exception as e:
                logging.error(f"Kalıcı bellek yükleme hatası: {e}")
        else:
            # Varsayılan kalıcı belleği kaydet
            self.save_permanent_memory()
        
        # Temporary memory yükleme
        if os.path.exists(self.temporary_memory_file):
            try:
                with open(self.temporary_memory_file, "r", encoding="utf-8") as file:
                    self.temporary_memory = json.load(file)
                logging.info("Geçici bellek başarıyla yüklendi.")
            except Exception as e:
                logging.error(f"Geçici bellek yükleme hatası: {e}")
        else:
            # Varsayılan geçici belleği kaydet
            self.save_temporary_memory()

    def save_permanent_memory(self):
        """Kalıcı belleği dosyaya kaydeder"""
        try:
            with open(self.permanent_memory_file, "w", encoding="utf-8") as file:
                json.dump(self.permanent_memory, file, ensure_ascii=False, indent=4)
            logging.info("Kalıcı bellek başarıyla kaydedildi.")
        except Exception as e:
            logging.error(f"Kalıcı bellek kaydetme hatası: {e}")

    def save_temporary_memory(self):
        """Geçici belleği dosyaya kaydeder"""
        try:
            with open(self.temporary_memory_file, "w", encoding="utf-8") as file:
                json.dump(self.temporary_memory, file, ensure_ascii=False, indent=4)
            logging.info("Geçici bellek başarıyla kaydedildi.")
        except Exception as e:
            logging.error(f"Geçici bellek kaydetme hatası: {e}")
    
    def setup_threads(self):
        """Thread'leri başlatır"""
        if self.state_thread is None or not self.state_thread.is_alive():
            self.state_thread = threading.Thread(target=self.monitor_state, daemon=True)
            self.state_thread.start()
        
        if self.reminder_thread is None or not self.reminder_thread.is_alive():
            self.reminder_thread = threading.Thread(target=self.check_reminders_loop, daemon=True)
            self.reminder_thread.start()
        
        if self.rules_thread is None or not self.rules_thread.is_alive():
            self.rules_thread = threading.Thread(target=self.run_rules_engine, daemon=True)
            self.rules_thread.start()
        
        if self.self_awareness_thread is None or not self.self_awareness_thread.is_alive():
            self.self_awareness_thread = threading.Thread(target=self.self_awareness_monitor, daemon=True)
            self.self_awareness_thread.start()
        
        if self.chat_mode == "sesli" and (self.hotword_thread is None or not self.hotword_thread.is_alive()):
            self.hotword_thread = threading.Thread(target=self.hotword_detection, daemon=True)
            self.hotword_thread.start()
    
    def load_rules(self):
        """Kural motorunu yükle"""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, "r", encoding="utf-8") as file:
                    self.rules_engine = json.load(file)
                logging.info("Kural motoru başarıyla yüklendi.")
            except Exception as e:
                logging.error(f"Kural motoru yükleme hatası: {e}")
        else:
            # Varsayılan kuralları kaydet
            self.save_rules()
    
    def save_rules(self):
        """Kural motorunu kaydet"""
        try:
            with open(self.rules_file, "w", encoding="utf-8") as file:
                json.dump(self.rules_engine, file, ensure_ascii=False, indent=4)
            logging.info("Kural motoru başarıyla kaydedildi.")
        except Exception as e:
            logging.error(f"Kural motoru kaydetme hatası: {e}")
    
    def add_rule(self, rule_name, condition, action):
        """Yeni bir kural ekle"""
        self.rules_engine[rule_name] = {
            "condition": condition,
            "action": action
        }
        self.save_rules()
        self.speak(f"{rule_name} kuralı başarıyla eklendi.")
        logging.info(f"Yeni kural eklendi: {rule_name}")

    def remove_rule(self, rule_name):
        """Bir kuralı kaldır"""
        if rule_name in self.rules_engine:
            del self.rules_engine[rule_name]
            self.save_rules()
            self.speak(f"{rule_name} kuralı başarıyla kaldırıldı.")
            logging.info(f"Kural kaldırıldı: {rule_name}")
        else:
            self.speak(f"{rule_name} adında bir kural bulunamadı.")
            logging.warning(f"Kural bulunamadı: {rule_name}")

    def run_rules_engine(self):
        """Kural motorunu çalıştır"""
        while True:
            for rule_name, rule in self.rules_engine.items():
                try:
                    if eval(rule["condition"]):
                        self.add_to_thinking_log("RulesEngine", f"{rule_name} kuralı çalıştırılıyor")
                        eval(rule["action"])
                except Exception as e:
                    logging.error(f"Kural çalıştırma hatası ({rule_name}): {e}")
            time.sleep(10)  # Her 10 saniyede bir kuralları kontrol et
    
    def get_hour(self):
        """Geçerli saati al"""
        return datetime.datetime.now().hour
    
    def get_minute(self):
        """Geçerli dakikayı al"""
        return datetime.datetime.now().minute
    
    def print_colored(self, text, color=Fore.WHITE):
        """Renkli metin yazdırır."""
        print(color + text + Style.RESET_ALL)
        logging.info(f"OUTPUT: {text}")

    def save_to_permanent_memory(self, key, value):
        """Kalıcı hafızaya bilgi kaydeder."""
        if key not in self.permanent_memory:
            self.permanent_memory[key] = []
        self.permanent_memory[key].append(value)
        self.save_permanent_memory()
        self.add_to_thinking_log("Memory", f"'{key}' anahtarı ile kalıcı belleğe bilgi kaydedildi")

    def save_to_temporary_memory(self, key, value):
        """Geçici hafızaya bilgi kaydeder."""
        if key not in self.temporary_memory:
            self.temporary_memory[key] = []
        self.temporary_memory[key].append(value)
        self.save_temporary_memory()
        self.add_to_thinking_log("Memory", f"'{key}' anahtarı ile geçici belleğe bilgi kaydedildi")

    def analyze_emotion(self, text):
        """Kullanıcının mesajındaki duyguyu analiz eder."""
        positive_words = ["mutlu", "sevindim", "teşekkür", "güzel", "harika", "iyi", "memnun", "keyifli", "hoş", "süper"]
        negative_words = ["üzgün", "kızgın", "sinirli", "kötü", "sıkıldım", "mutsuz", "yorgun", "bezgin", "endişeli", "stresli"]
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def respond_with_emotion(self, text):
        """Duyguya göre tepki verir."""
        emotion = self.analyze_emotion(text)
        
        # Duygusal durumu kaydet
        self.temporary_memory["current_session"]["emotion_log"].append({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text,
            "emotion": emotion
        })
        self.save_temporary_memory()
        
        if emotion == "positive":
            self.speak("Ne güzel! Mutlu olduğunu duymak beni de mutlu ediyor.")
        elif emotion == "negative":
            self.speak("Üzgünüm, böyle hissettiğin için. Yanındayım.")
        else:
            self.speak("Anlıyorum. Nasıl yardımcı olabilirim?")

    def speak(self, text):
        """Metni sesli olarak okur ve space tuşu ile kesmeyi sağlar."""
        clean_text = self.remove_emojis(text)
        self.print_colored(f"Asena: {text}", Fore.GREEN)
        
        # Konuşma süresini ölç
        start_time = time.time()
        
        self.last_interaction_time = time.time()
        
        if self.is_sleeping:
            self.is_sleeping = False
            self.print_colored("Asena uyandı.", Fore.YELLOW)
        
        # Konuşmayı başlat
        self.engine.say(clean_text)
        
        # Konuşmayı kesme işlevi
        while self.engine.isBusy():
            try:
                if keyboard.is_pressed('space'):
                    self.engine.stop()  # Konuşmayı durdur
                    break
                time.sleep(0.1)
            except Exception as e:
                logging.error(f"Konuşma dinleme hatası: {e}")
                break
        
        # Artık engine.endLoop() kullanmanıza gerek yok
        # runAndWait() işlemi tamamlanana kadar bekler, o yüzden manuel döngü sonlandırma gerekmez
        self.engine.runAndWait()  # Bu komut, konuşmanın tamamlanmasını bekler
        
        # İstatistikleri güncelle
        response_time = time.time() - start_time
        if self.response_time_start > 0:
            total_response_time = time.time() - self.response_time_start
            self.add_to_thinking_log("Metrics", f"Yanıt süresi: {total_response_time:.2f} saniye")
            
            # Performans metriklerini güncelle
            old_avg = self.self_awareness["performance_metrics"]["response_time_avg"]
            interactions = self.self_awareness["performance_metrics"]["total_interactions"]
            
            # İlk etkileşim için özel durum
            if interactions == 0:
                new_avg = total_response_time
            else:
                new_avg = (old_avg * interactions + total_response_time) / (interactions + 1)
                
            self.self_awareness["performance_metrics"]["response_time_avg"] = new_avg
            self.self_awareness["performance_metrics"]["total_interactions"] += 1
            self.self_awareness["performance_metrics"]["successful_interactions"] += 1
            
        self.response_time_start = 0

    def remove_emojis(self, text):
        """Metinden emoji karakterlerini temizler."""
        emoji_pattern = re.compile("["u"\U0001F600-\U0001F64F"  # emoticons
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
        self.last_interaction_time = time.time()
        self.response_time_start = time.time()  # Yanıt süresini ölçmeye başla
        
        if self.is_sleeping:
            self.is_sleeping = False
            self.print_colored("Asena uyandı.", Fore.YELLOW)
        
        try:
            with sr.Microphone() as source:
                self.print_colored("Asena dinliyor...", Fore.BLUE)
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)
            
            try:
                text = self.recognizer.recognize_google(audio, language="tr-TR")
                self.print_colored(f"Sen (Sesli): {text}", Fore.CYAN)
                return text
            except sr.UnknownValueError:
                if not self.is_sleeping:
                    self.speak("Seni anlayamadım, tekrar eder misin?")
                return ""
            except sr.RequestError:
                if not self.is_sleeping:
                    self.speak("Ses tanıma servisine ulaşılamıyor.")
                self.self_awareness["performance_metrics"]["failed_interactions"] += 1
                return ""
        except Exception as e:
            logging.error(f"Mikrofon hatası: {e}")
            self.speak("Mikrofon ile ilgili bir sorun oluştu.")
            return ""
    
    def hotword_detection(self):
        """Arka planda sürekli çalışan bir thread ile 'asena' kelimesini dinler"""
        while True:
            if self.is_sleeping and self.chat_mode == "sesli":
                try:
                    with sr.Microphone() as source:
                        self.print_colored("Hotword bekleniyor... ('asena' deyin)", Fore.BLUE)
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
                    self.print_colored(f"Hotword dinleme hatası: {e}", Fore.RED)
                    logging.error(f"Hotword dinleme hatası: {e}")
                    time.sleep(1)
            time.sleep(0.1)  # CPU yükünü azaltmak için kısa bir bekleme
    
    def monitor_state(self):
        """Asistan durumunu izler, uyku moduna geçiş yapar ve kendi kendine konuşur"""
        while True:
            current_time = time.time()
            
            # Uyku modunu kontrol et
            if not self.is_sleeping and (current_time - self.last_interaction_time > self.sleep_timeout):
                self.is_sleeping = True
                self.print_colored("Asena uyku moduna geçti. 'Asena' diyerek uyandırabilirsiniz.", Fore.YELLOW)
                logging.info("Asena uyku moduna geçti")
            
            # Kendi kendine konuşma
            if not self.is_sleeping and (current_time - self.last_self_talk_time > self.self_talk_interval):
                self.self_talk()
                self.last_self_talk_time = current_time
            
            time.sleep(1)  # CPU yükünü azaltmak için
    
    def self_awareness_monitor(self):
        """Öz farkındalık metriklerini düzenli olarak günceller"""
        while True:
            try:
                # Bellek istatistiklerini güncelle
                self.self_awareness["memory_stats"]["permanent_memory_size"] = len(json.dumps(self.permanent_memory))
                self.self_awareness["memory_stats"]["temporary_memory_size"] = len(json.dumps(self.temporary_memory))
                self.self_awareness["memory_stats"]["short_term_items"] = len(self.temporary_memory["short_term_memory"])
                
                # Sistem istatistiklerini güncelle
                self.self_awareness["system_stats"]["cpu_usage"] = psutil.cpu_percent()
                self.self_awareness["system_stats"]["memory_usage"] = psutil.virtual_memory().percent
                
                # Oturum başlangıç zamanını datetime nesnesine dönüştür
                start_time_str = self.temporary_memory["current_session"]["start_time"]
                start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.datetime.now()
                
                # Uptime hesapla (saniye cinsinden)
                uptime_seconds = (now - start_time).total_seconds()
                self.self_awareness["system_stats"]["uptime"] = uptime_seconds
                
                # Belleği disk üzerine kaydet
                self.save_permanent_memory()
                self.save_temporary_memory()
                
                self.add_to_thinking_log("SelfAwareness", "Öz farkındalık metrikleri güncellendi")
                time.sleep(60)  # Her dakika güncelle
            except Exception as e:
                logging.error(f"Öz farkındalık monitörü hatası: {e}")
                time.sleep(5)  # Hata durumunda kısa süre bekle
    
    def add_to_thinking_log(self, category, thought):
        """Düşünme günlüğüne bir düşünce ekler"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.temporary_memory["thinking_log"].append({
                "timestamp": timestamp,
                "category": category,
                "thought": thought
            })
            
            # Düşünme günlüğünü 100 kayıtla sınırla
            if len(self.temporary_memory["thinking_log"]) > 100:
                self.temporary_memory["thinking_log"] = self.temporary_memory["thinking_log"][-100:]
            
            self.save_temporary_memory()
        except Exception as e:
            logging.error(f"Düşünme günlüğüne eklerken hata: {e}")
    
    def self_talk(self):
        """Asistan kendi kendine konuşma yapar"""
        try:
            # Önce düşünme günlüğüne bir düşünce ekle
            self.add_to_thinking_log("SelfTalk", "Kullanıcıya bir şey söylemeye hazırlanıyorum...")

            # Yapay zeka gibi düşünüyor hissi vermek için analiz yap
            now = datetime.datetime.now()
            hour = now.hour
            weekday = now.weekday()

            # Gün ve saat bilgisine göre konuşma tipini belirle
            if hour < 9 or hour > 21:
                talk_type = random.choice(["saat", "motivasyon", "hatırlatıcı"])
            elif weekday >= 5:  # Hafta sonu
                talk_type = random.choice(["hava", "öneri", "motivasyon", "hatırlatıcı"])
            else:  # Hafta içi
                talk_type = random.choice(["hava", "saat", "haber", "hatırlatıcı", "motivasyon", "öneri"])

            if talk_type == "hava":
                self.speak("Size güncel hava durumu bilgisi sunuyorum.")
                self.get_weather()
            elif talk_type == "saat":
                current_time = datetime.datetime.now().strftime("%H:%M")
                day_name = self.get_turkish_day_name(datetime.datetime.now().weekday())
                self.speak(f"Şu anda saat {current_time}. Bugün {day_name}. Zamanınızı verimli kullanmanızı dilerim.")
            elif talk_type == "haber":
                self.speak("Size güncel haberlerden bazılarını sunuyorum:")
                self.read_news()
            elif talk_type == "hatırlatıcı":
                if "reminders" in self.permanent_memory and self.permanent_memory["reminders"]:
                    upcoming = self.get_upcoming_reminders(1)
                    if upcoming:
                        reminder = upcoming[0]
                        reminder_time = datetime.datetime.strptime(reminder["date"], "%Y-%m-%d %H:%M:%S")
                        now = datetime.datetime.now()
                        time_diff = reminder_time - now

                        if time_diff.days > 0:
                            time_str = f"{time_diff.days} gün sonra"
                        elif time_diff.seconds // 3600 > 0:
                            time_str = f"{time_diff.seconds // 3600} saat sonra"
                        else:
                            time_str = f"{time_diff.seconds // 60} dakika sonra"

                        self.speak(f"Size yaklaşan bir hatırlatma: {reminder['text']} - {time_str}.")
                    else:
                        self.speak("Şu anda aktif bir hatırlatıcıyınız bulunmuyor. Yeni bir hatırlatıcı eklemek ister misiniz?")
                else:
                    self.speak("Henüz hiç hatırlatıcı eklememişsiniz. Size bir hatırlatıcı ayarlamak için 'hatırlatıcı ekle' diyebilirsiniz.")
            elif talk_type == "motivasyon":
                motivational_quotes = [
                    "Bugün yapabileceğiniz en küçük adım bile sizi hedefinize bir adım daha yaklaştırır.",
                    "Başarı, küçük çabaların sürekli tekrarlanmasıyla gelir.",
                    "Zorluklar, güçlü yönlerinizi keşfetmenin bir yoludur.",
                    "Kendinize inanmak, başarının yarısıdır.",
                    "Her başarısızlık, başarıya giden yolda bir derstir."
                ]
                self.speak(random.choice(motivational_quotes))
            elif talk_type == "öneri":
                productivity_tips = [
                    "Çalışırken düzenli molalar vermek verimliliği artırır.",
                    "Gün içinde 10 dakikalık kısa yürüyüşler enerji seviyenizi yükseltebilir.",
                    "Yeterli su içmek, zihinsel performansınızı artırmanın basit bir yoludur.",
                    "Günlük hedeflerinizi bir liste halinde yazmanız, odaklanmanızı sağlar.",
                    "Telefon bildirimlerini kapatmak, dikkat dağınıklığını azaltır."
                ]
                self.speak(random.choice(productivity_tips))

        except Exception as e:
            print(f"Hata oluştu: {e}")
    
    def check_reminders(self):
        """Hatırlatıcıları sürekli kontrol eden thread"""
        while True:
            current_time = datetime.datetime.now()
            if "reminders" in self.permanent_memory:
                triggered_reminders = []
            
                for reminder in self.permanent_memory["reminders"]:
                    # Hatırlatıcının 'date' alanı olup olmadığını kontrol et
                    if "date" not in reminder:
                        self.print_colored("Uyarı: Hatırlatıcıda 'date' bilgisi yok. Bu hatırlatıcıyı atlıyorum.", Fore.YELLOW)
                        continue  # Bu hatırlatıcıyı atla
                
                    try:
                        reminder_time = datetime.datetime.strptime(reminder["date"], "%Y-%m-%d %H:%M:%S")
                        if current_time >= reminder_time and not reminder.get("triggered", False):
                            # Hatırlatıcı zamanı geldi ve henüz tetiklenmedi
                            if not self.is_sleeping:
                                self.speak(f"Hatırlatıcı: {reminder['text']}")
                            reminder["triggered"] = True
                            triggered_reminders.append(reminder)
                    except ValueError as e:
                        self.print_colored(f"Hatırlatıcı tarihi geçersiz: {reminder['date']}. Hata: {e}", Fore.RED)
                        continue  # Geçersiz tarihli hatırlatıcıyı atla
            
                # Tetiklenen hatırlatıcıları güncel olarak işaretle
                    if triggered_reminders:
                        self.save_permanent_memory()
        
            time.sleep(10)  # Her 10 saniyede bir kontrol et


    def add_reminder(self, text, date):
        """Yeni bir hatırlatıcı ekler."""
        if "reminders" not in self.permanent_memory:
            self.permanent_memory["reminders"] = []
    
        try:
            # Tarih formatını kontrol et
            datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            self.permanent_memory["reminders"].append({
                "text": text,
                "date": date,
                "triggered": False
            })
            self.save_permanent_memory()
            self.speak(f"'{text}' hatırlatıcısı {date} tarihine eklendi.")
        except ValueError as e:
            self.speak(f"Geçersiz tarih formatı. Lütfen tarihi 'YYYY-MM-DD HH:MM:SS' formatında girin.")
    

    def read_news(self):
        """RSS'den haber okur"""
        try:
            feed = feedparser.parse(self.news_url)
            
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                self.speak("Güncel haberlerden bazıları:")
                max_news = min(3, len(feed.entries))
                
                for i, entry in enumerate(feed.entries[:max_news]):
                    if hasattr(entry, 'title'):
                        title = re.sub('<.*?>', '', entry.title)
                        self.speak(f"{i+1}. {title}")
                    else:
                        self.print_colored(f"Haber {i+1} için başlık bulunamadı", Fore.RED)
            else:
                self.speak("Haberlere şu anda erişemiyorum.")
                self.print_colored("RSS içeriği inceleniyor:", Fore.RED)
                self.print_colored(f"Feed status: {feed.get('status', 'Bilinmiyor')}", Fore.RED)
                self.print_colored(f"Version: {feed.get('version', 'Bilinmiyor')}", Fore.RED)
                self.print_colored(f"Entries sayısı: {len(feed.get('entries', []))}", Fore.RED)
                
                # Alternatif RSS kaynağı dene
                self.speak("Alternatif haber kaynağı deneniyor...")
                alternate_feed = feedparser.parse("http://www.hurriyet.com.tr/rss/anasayfa")
                
                if hasattr(alternate_feed, 'entries') and len(alternate_feed.entries) > 0:
                    self.speak("Alternatif kaynaktan haberler:")
                    max_news = min(3, len(alternate_feed.entries))
                    for i, entry in enumerate(alternate_feed.entries[:max_news]):
                        if hasattr(entry, 'title'):
                            title = re.sub('<.*?>', '', entry.title)
                            self.speak(f"{i+1}. {title}")
                else:
                    self.speak("Haber kaynaklarına erişim şu anda mümkün değil. Daha sonra tekrar deneyeceğim.")
        except Exception as e:
            self.speak("Haberleri okurken bir sorun oluştu.")
            self.print_colored(f"Haber okuma hatası: {e}", Fore.RED)
            self.print_colored("Hata detayları:", Fore.RED)
            self.print_colored(str(e), Fore.RED)
    
    def load_memory(self):
        """Kaydedilmiş bellekleri yükler"""
        # Kalıcı belleği yükle
        if os.path.exists(self.permanent_memory_file):
            try:
                with open(self.permanent_memory_file, "r", encoding="utf-8") as file:
                    loaded_memory = json.load(file)
                    
                    # Eksik anahtarları kontrol et ve ekle
                    for key in ["user_info", "contacts", "reminders", "preferences"]:
                        if key not in loaded_memory:
                            if key in ["user_info", "contacts", "preferences"]:
                                loaded_memory[key] = {}
                            else:
                                loaded_memory[key] = []
                    
                    self.permanent_memory = loaded_memory
                    self.print_colored("Kalıcı bellek başarıyla yüklendi.", Fore.GREEN)
            except Exception as e:
                self.print_colored(f"Kalıcı bellek yükleme hatası: {e}", Fore.RED)
                # Bellek dosyasını yedekle
                if os.path.exists(self.permanent_memory_file):
                    os.rename(self.permanent_memory_file, 
                             f"asena_permanent_memory_backup_{int(time.time())}.json")
                # Yeni bir kalıcı bellek oluştur
                self.save_permanent_memory()
                self.print_colored("Yeni bir kalıcı bellek oluşturuldu.", Fore.GREEN)
        else:
            # Dosya yoksa oluştur
            self.save_permanent_memory()
            self.print_colored("Kalıcı bellek dosyası oluşturuldu.", Fore.GREEN)
        
        # Geçici belleği yükle
        if os.path.exists(self.temporary_memory_file):
            try:
                with open(self.temporary_memory_file, "r", encoding="utf-8") as file:
                    loaded_memory = json.load(file)
                    
                    # Eksik anahtarları kontrol et ve ekle
                    for key in ["messages", "current_session", "short_term_memory"]:
                        if key not in loaded_memory:
                            if key == "current_session":
                                loaded_memory[key] = {
                                    "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "interactions": 0
                                }
                            else:
                                loaded_memory[key] = []
                    
                    self.temporary_memory = loaded_memory
                    self.print_colored("Geçici bellek başarıyla yüklendi.", Fore.GREEN)
            except Exception as e:
                self.print_colored(f"Geçici bellek yükleme hatası: {e}", Fore.RED)
                # Bellek dosyasını yedekle
                if os.path.exists(self.temporary_memory_file):
                    os.rename(self.temporary_memory_file, 
                             f"asena_temporary_memory_backup_{int(time.time())}.json")
                # Yeni bir geçici bellek oluştur
                self.save_temporary_memory()
                self.print_colored("Yeni bir geçici bellek oluşturuldu.", Fore.GREEN)
        else:
            # Dosya yoksa oluştur
            self.save_temporary_memory()
            self.print_colored("Geçici bellek dosyası oluşturuldu.", Fore.GREEN)



    
    
    def save_permanent_memory(self):
        """Kalıcı belleği dosyaya kaydeder"""
        try:
            with open(self.permanent_memory_file, "w", encoding="utf-8") as file:
                json.dump(self.permanent_memory, file, ensure_ascii=False, indent=4)
            self.print_colored("Kalıcı bellek başarıyla kaydedildi.", Fore.GREEN)
            return True
        except Exception as e:
            self.print_colored(f"Kalıcı bellek kaydetme hatası: {e}", Fore.RED)
            return False
            
    def save_temporary_memory(self):
        """Geçici belleği dosyaya kaydeder"""
        try:
            with open(self.temporary_memory_file, "w", encoding="utf-8") as file:
                json.dump(self.temporary_memory, file, ensure_ascii=False, indent=4)
            self.print_colored("Geçici bellek başarıyla kaydedildi.", Fore.GREEN)
            return True
        except Exception as e:
            self.print_colored(f"Geçici bellek kaydetme hatası: {e}", Fore.RED)
            return False
    
    def extract_user_info(self, text):
        """Kullanıcıdan önemli bilgileri çıkarır ve kalıcı bellekte saklar"""
        
        # İsim tanıma
        name_patterns = [
            r"(benim adım|ismim) ([A-Za-zÇçĞğİıÖöŞşÜü]+)",
            r"(ben) ([A-Za-zÇçĞğİıÖöŞşÜü]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(2)
                if "name" not in self.permanent_memory["user_info"] or self.permanent_memory["user_info"]["name"] != name:
                    self.permanent_memory["user_info"]["name"] = name
                    self.add_to_short_term_memory(f"Kullanıcının adı: {name}")
        
        # Yaş tanıma
        age_patterns = [
            r"(yaşım|ben) (\d+) yaşında(yım)?",
            r"(\d+) yaşında(yım)?"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = match.group(2)
                if "age" not in self.permanent_memory["user_info"] or self.permanent_memory["user_info"]["age"] != age:
                    self.permanent_memory["user_info"]["age"] = age
                    self.add_to_short_term_memory(f"Kullanıcının yaşı: {age}")
        
        # İş tanıma
        job_patterns = [
            r"(ben bir|işim|mesleğim) ([A-Za-zÇçĞğİıÖöŞşÜü]+)",
            r"(ben) ([A-Za-zÇçĞğİıÖöŞşÜü]+) (olarak çalışıyorum)"
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                job = match.group(2)
                if "job" not in self.permanent_memory["user_info"] or self.permanent_memory["user_info"]["job"] != job:
                    self.permanent_memory["user_info"]["job"] = job
                    self.add_to_short_term_memory(f"Kullanıcının mesleği: {job}")
        
        # Tercihler
        like_pattern = r"(ben|benim) ([A-Za-zÇçĞğİıÖöŞşÜü]+) (sev|beğen)"
        match = re.search(like_pattern, text, re.IGNORECASE)
        if match:
            liked_thing = match.group(2)
            if "likes" not in self.permanent_memory["user_info"]:
                self.permanent_memory["user_info"]["likes"] = []
            if liked_thing not in self.permanent_memory["user_info"]["likes"]:
                self.permanent_memory["user_info"]["likes"].append(liked_thing)
                self.add_to_short_term_memory(f"Kullanıcı {liked_thing} seviyor")
        
        # Hoşlanmadıkları
        dislike_pattern = r"(ben|benim) ([A-Za-zÇçĞğİıÖöŞşÜü]+) (sevmiyorum|hoşlanmıyorum)"
        match = re.search(dislike_pattern, text, re.IGNORECASE)
        if match:
            disliked_thing = match.group(2)
            if "dislikes" not in self.permanent_memory["user_info"]:
                self.permanent_memory["user_info"]["dislikes"] = []
            if disliked_thing not in self.permanent_memory["user_info"]["dislikes"]:
                self.permanent_memory["user_info"]["dislikes"].append(disliked_thing)
                self.add_to_short_term_memory(f"Kullanıcı {disliked_thing} sevmiyor")
                
        # Değişiklikleri kaydet
        self.save_permanent_memory()
    
    def add_to_short_term_memory(self, info):
        """Kısa süreli belleğe bilgi ekler (son 20 bilgi)"""
        if "short_term_memory" not in self.temporary_memory:
            self.temporary_memory["short_term_memory"] = []
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.temporary_memory["short_term_memory"].append({"info": info, "timestamp": timestamp})
        
        # Kısa süreli belleği 20 girişle sınırla
        if len(self.temporary_memory["short_term_memory"]) > 20:
            self.temporary_memory["short_term_memory"].pop(0)  # En eski girişi sil
            
        # Değişiklikleri kaydet
        self.save_temporary_memory()
    
    def get_memory_context(self):
        """Kullanıcı bilgilerini ve kısa süreli hafızayı içeren bağlam metni oluşturur"""
        context = "Kullanıcı hakkında bilgiler:\n"
        
        # Kullanıcı bilgilerini ekle
        if "user_info" in self.permanent_memory and self.permanent_memory["user_info"]:
            for key, value in self.permanent_memory["user_info"].items():
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
        if "short_term_memory" in self.temporary_memory and self.temporary_memory["short_term_memory"]:
            recent_memories = self.temporary_memory["short_term_memory"][-5:]
            for memory in recent_memories:
                context += f"- {memory['info']}\n"
        
        # Yaklaşan hatırlatıcılar
        if "reminders" in self.permanent_memory and self.permanent_memory["reminders"]:
            upcoming = self.get_upcoming_reminders(3)  # En yakın 3 hatırlatıcı
            if upcoming:
                context += "\nYaklaşan hatırlatıcılar:\n"
                for reminder in upcoming:
                    context += f"- {reminder['text']} ({reminder['date']})\n"
        
        return context
    
    def get_upcoming_reminders(self, count=3):
        """Yaklaşan hatırlatıcıları döndürür"""
        now = datetime.datetime.now()
        upcoming = []
        
        for reminder in self.permanent_memory["reminders"]:
            # Tetiklenmiş hatırlatıcıları atla
            if reminder.get("triggered", False):
                continue
                
            reminder_time = datetime.datetime.strptime(reminder["date"], "%Y-%m-%d %H:%M:%S")
            # Gelecekte olan hatırlatıcıları al
            if reminder_time > now:
                upcoming.append(reminder)
        
        # Tarihe göre sırala
        upcoming.sort(key=lambda x: datetime.datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"))
        
        # İstenilen sayıda hatırlatıcı döndür
        return upcoming[:count]
    
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
            "content": f"Sen Asena, Türkçe konuşan bir kişisel asistansın. Amacın Nuriye her türlü yardımcı olmak. Konular hakkında görüşe sahip olmalısın. Kısa cümleler kur. Espri anlayışına sahip ol ve gerektiği yerde en yakın arkadaşı ol. Kullanıcı hakkında şunları biliyorsun:\n{context}"
        }
        
        # Geçici belleğe etkileşimi kaydet
        self.temporary_memory["current_session"]["interactions"] += 1
        
        # Eğer sistem mesajı yoksa ekle
        if not any(msg.get("role") == "system" for msg in self.temporary_memory["messages"]):
            self.temporary_memory["messages"].insert(0, system_message)
        else:
            # Sistem mesajını güncelle
            for idx, msg in enumerate(self.temporary_memory["messages"]):
                if msg.get("role") == "system":
                    self.temporary_memory["messages"][idx] = system_message
                    break
        
        # Kullanıcı mesajını ekle
        self.temporary_memory["messages"].append({"role": "user", "content": user_input})
        
        # Mesaj geçmişini son 10 mesajla sınırla (sistem mesajı dışında)
        if len(self.temporary_memory["messages"]) > 11:  # 1 sistem mesajı + 10 konuşma mesajı
            # Sistem mesajını koru
            system_msg = next((msg for msg in self.temporary_memory["messages"] if msg.get("role") == "system"), None)
            # Diğer mesajları filtrele ve son 10'u al
            other_msgs = [msg for msg in self.temporary_memory["messages"] if msg.get("role") != "system"][-10:]
            # Yeni mesaj listesini oluştur
            self.temporary_memory["messages"] = [system_msg] + other_msgs if system_msg else other_msgs
        
        data = {
            "model": "google/gemini-2.0-pro-exp-02-05:free",
            "messages": self.temporary_memory["messages"]
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                self.speak(reply)
                
                self.temporary_memory["messages"].append({"role": "assistant", "content": reply})
                self.save_temporary_memory()
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
        if "contacts" not in self.permanent_memory:
            self.permanent_memory["contacts"] = {}
            self.save_permanent_memory()
        
        if contact_name.lower() not in self.permanent_memory["contacts"]:
            self.speak(f"{contact_name} adlı kişi kayıtlı değil. Lütfen önce kişiyi kaydedin.")
            return
        
        contact = self.permanent_memory["contacts"][contact_name.lower()]
        
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
        if "contacts" not in self.permanent_memory:
            self.permanent_memory["contacts"] = {}
        
        self.permanent_memory["contacts"][name.lower()] = {
            "name": name,
            "email": email,
            "phone": phone
        }
        self.save_permanent_memory()
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
            if "user_info" in self.permanent_memory and "name" in self.permanent_memory["user_info"]:
                self.speak(f"Evet, adınız {self.permanent_memory['user_info']['name']}.")
            else:
                self.speak("Henüz adınızı bilmiyorum. Bana adınızı söyleyebilirsiniz.")
            return True
        
        elif "ben kimim" in command:
            if "user_info" in self.permanent_memory and self.permanent_memory["user_info"]:
                info = self.permanent_memory["user_info"]
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
        self.print_colored("Merhaba! Ben Asena. Size nasıl yardımcı olabilirim?", Fore.GREEN)
        
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
                    user_input = input(Fore.BLUE + "Sen (Yazılı): " + Style.RESET_ALL)
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["çık", "kapat", "görüşürüz"]:
                    self.print_colored("Görüşmek üzere!", Fore.YELLOW)
                    break
                    
                # Özel komutları kontrol et
                if not self.process_command(user_input):
                    # Eğer özel komut değilse normal sohbet et
                    self.chat_with_asena(user_input)
                    
            except KeyboardInterrupt:
                self.print_colored("Görüşmek üzere!", Fore.YELLOW)
                break
            except Exception as e:
                self.print_colored(f"Bir hata oluştu: {e}", Fore.RED)
                continue



    def asena_function(user_input):
        # Burada basit bir yanıt döndürüyoruz, ancak yapay zekânız daha gelişmiş olabilir.
        if 'merhaba' in user_input.lower():
            return "Merhaba! Size nasıl yardımcı olabilirim?"
        elif 'nasılsın' in user_input.lower():
            return "Ben bir yapay zekâyım, her zaman hazırım!"
        else:
            return "Üzgünüm, anlamadım. Başka bir şey sorabilirsiniz."


 



class MemoryManager:
    def __init__(self, permanent_memory_file, temporary_memory_file):
        self.permanent_memory_file = permanent_memory_file
        self.temporary_memory_file = temporary_memory_file
        
        self.permanent_memory = self.load_memory(self.permanent_memory_file, default={})
        self.temporary_memory = self.load_memory(self.temporary_memory_file, default={})
        
    def load_memory(self, file_path, default):
        """ Bellek dosyalarını yükler veya varsayılan bir yapı oluşturur."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e:
                logging.error(f"{file_path} yüklenirken hata oluştu: {e}")
        return default
    
    def save_memory(self, file_path, data):
        """ Belleği dosyaya kaydeder."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"{file_path} kaydedilirken hata oluştu: {e}")
    
    def add_to_permanent_memory(self, key, value):
        """ Kalıcı belleğe veri ekler."""
        self.permanent_memory[key] = value
        self.save_memory(self.permanent_memory_file, self.permanent_memory)
    
    def add_to_temporary_memory(self, key, value, expire_minutes=30):
        """ Geçici belleğe veri ekler ve süre sonunda temizler."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.temporary_memory[key] = {"value": value, "timestamp": timestamp, "expire": expire_minutes}
        self.save_memory(self.temporary_memory_file, self.temporary_memory)
    
    def clean_expired_temporary_memory(self):
        """ Süresi dolmuş geçici bellek kayıtlarını temizler."""
        now = datetime.datetime.now()
        for key, data in list(self.temporary_memory.items()):
            if isinstance(data, dict) and "timestamp" in data:
                try:
                    stored_time = datetime.datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if (now - stored_time).total_seconds() > data["expire"] * 60:
                        del self.temporary_memory[key]
                except Exception as e:
                    logging.error(f"Bellek temizleme hatası ({key}): {e}")
        self.save_memory(self.temporary_memory_file, self.temporary_memory)
    
    def analyze_memory_usage(self):
        """ Bellek kullanımını analiz eder ve eski verileri temizler."""
        self.clean_expired_temporary_memory()
        memory_size = len(json.dumps(self.permanent_memory))
        if memory_size > 50000:  # 50 KB üzerindeyse temizlik yap
            keys_to_delete = list(self.permanent_memory.keys())[:5]
            for key in keys_to_delete:
                del self.permanent_memory[key]
            self.save_memory(self.permanent_memory_file, self.permanent_memory)

# Örnek kullanım
if __name__ == "__main__":
    memory_manager = MemoryManager("asena_permanent_memory.json", "asena_temporary_memory.json")
    memory_manager.add_to_permanent_memory("kullanici_adi", "Ahmet")
    memory_manager.add_to_temporary_memory("son_sesli_komut", "Hava nasıl?", expire_minutes=10)
    memory_manager.analyze_memory_usage()


class SystemController:
    def __init__(self):
        self.os_type = platform.system()
        self.setup_audio()
        self.setup_lights()
        self.brightness_controller = sbc
        
    def setup_audio(self):
        """Ses kontrolü için başlangıç ayarları"""
        try:
            if self.os_type == "Windows":
                self.audio_device = comtypes.client.CreateObject("WScript.Shell")
            else:
                # Linux için alternatif ses kontrolü
                import alsaaudio
                self.audio_device = alsaaudio.Mixer()
        except Exception as e:
            print(f"Ses kontrolü başlatılamadı: {e}")
    
    def setup_lights(self):
        """Philips Hue ışıkları için başlangıç ayarları"""
        try:
            # Bridge IP adresini konfigürasyon dosyasından oku
            with open("config.json", "r") as f:
                config = json.load(f)
                bridge_ip = config.get("hue_bridge_ip", "192.168.1.2")
            
            self.bridge = Bridge(bridge_ip)
            # İlk kullanımda bridge'e bağlanmak için butona basılması gerekir
            self.bridge.connect()
        except Exception as e:
            print(f"Işık kontrolü başlatılamadı: {e}")
    
    def control_volume(self, action="get", value=None):
        """Ses seviyesi kontrolü
        
        Args:
            action (str): "get", "set", "up", "down", "mute"
            value (int): 0-100 arası ses seviyesi
        """
        try:
            if self.os_type == "Windows":
                if action == "up":
                    self.audio_device.SendKeys(chr(175)) # Volume Up
                elif action == "down":
                    self.audio_device.SendKeys(chr(174)) # Volume Down
                elif action == "mute":
                    self.audio_device.SendKeys(chr(173)) # Mute
                elif action == "set" and value is not None:
                    # WMI ile ses seviyesini ayarla
                    c = wmi.WMI()
                    vol = c.Win32_SoundDevice()[0]
                    vol.SetVolume(value)
                    
            else:  # Linux için
                if action == "get":
                    return self.audio_device.getvolume()[0]
                elif action == "set" and value is not None:
                    self.audio_device.setvolume(value)
                elif action == "mute":
                    self.audio_device.setmute(1)
                    
        except Exception as e:
            print(f"Ses kontrolü hatası: {e}")
    
    def control_brightness(self, action="get", value=None):
        """Ekran parlaklığı kontrolü
        
        Args:
            action (str): "get", "set", "up", "down"
            value (int): 0-100 arası parlaklık değeri
        """
        try:
            current = self.brightness_controller.get_brightness()[0]
            
            if action == "get":
                return current
            elif action == "set" and value is not None:
                self.brightness_controller.set_brightness(value)
            elif action == "up":
                new_value = min(current + 10, 100)
                self.brightness_controller.set_brightness(new_value)
            elif action == "down":
                new_value = max(current - 10, 0)
                self.brightness_controller.set_brightness(new_value)
                
        except Exception as e:
            print(f"Parlaklık kontrolü hatası: {e}")
    
    def control_room_lights(self, action="get", room="bedroom", value=None):
        """Oda ışıklarının kontrolü
        
        Args:
            action (str): "get", "set", "on", "off"
            room (str): Oda adı
            value (int): 0-100 arası parlaklık değeri
        """
        try:
            # Odadaki tüm ışıkları al
            lights = self.bridge.get_light_objects('name')
            room_lights = [light for name, light in lights.items() 
                         if room.lower() in name.lower()]
            
            if action == "get":
                return [light.brightness for light in room_lights]
            elif action == "on":
                for light in room_lights:
                    light.on = True
            elif action == "off":
                for light in room_lights:
                    light.on = False
            elif action == "set" and value is not None:
                for light in room_lights:
                    light.brightness = value
                    
        except Exception as e:
            print(f"Işık kontrolü hatası: {e}")


            

if __name__ == "__main__":
    asena = AsenaAssistant()
    asena.run()
