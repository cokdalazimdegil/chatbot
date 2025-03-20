from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import datetime
import os
from asena import AsenaAssistant  # Asena sınıfını import ediyoruz

app = Flask(__name__)
app.config['SECRET_KEY'] = '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'
socketio = SocketIO(app)

# Asena'yı başlat
asena = AsenaAssistant()

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('status_update', {
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'volume': asena.get_volume() if hasattr(asena, 'get_volume') else 50,
        'brightness': asena.get_brightness() if hasattr(asena, 'get_brightness') else 50
    })

@socketio.on('send_command')
def handle_command(data):
    try:
        command = data['command']
        print(f"Komut alındı: {command}")
        
        if not hasattr(asena, 'process_text'):
            print("process_text metodu bulunamadı")
            emit('response', {'response': 'Asena henüz hazır değil'})
            return
            
        response = asena.process_text(command)
        print(f"Yanıt: {response}")
        
        if response is None or response is False:
            emit('response', {'response': 'Anlayamadım, lütfen tekrar eder misiniz?'})
        else:
            emit('response', {'response': str(response)})
            
    except Exception as e:
        print(f"Hata: {str(e)}")
        emit('response', {'response': f'Bir hata oluştu: {str(e)}'})


@socketio.on('get_status')
def handle_status():
    try:
        # Asena'dan güncel durumu al
        volume = asena.get_volume() if hasattr(asena, 'get_volume') else 50
        brightness = asena.get_brightness() if hasattr(asena, 'get_brightness') else 50
        
        emit('status_update', {
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'volume': volume,
            'brightness': brightness
        })
    except Exception as e:
        print(f"Status hatası: {str(e)}")
        emit('status_update', {
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'volume': 50,
            'brightness': 50,
            'error': str(e)
        })

if __name__ == '__main__':
    print("Web sunucusu başlatılıyor...")
    print("Asena hazır ve bağlantı bekliyor...")
    print("http://localhost:5000 adresinden erişebilirsiniz.")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
