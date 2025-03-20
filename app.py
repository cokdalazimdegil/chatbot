from flask import Flask, request, jsonify
import json
from asena import asena_function


app = Flask(__name__)

@app.route('/')
def home():
    return "Asena Web Uygulamasına Hoş Geldiniz!"

@app.route('/ask', methods=['POST'])
def ask_asena():
    # Kullanıcının sorusunu JSON formatında alıyoruz
    user_input = request.json.get('input', '')
    
    # Asena'nın yanıtını alıyoruz
    response = asena_function(user_input)  # asena.py'deki işlevi burada çağırıyoruz

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
