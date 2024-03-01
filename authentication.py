from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import ObjectId
from dotenv import load_dotenv
import bcrypt
import urllib
import jwt
import datetime
import os
import sys

load_dotenv()

secret_key = os.getenv('SECRETKEY')

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = secret_key
app.config['MONGO_URI'] = "mongodb://" + urllib.parse.quote_plus(sys.argv[1]) + ":"\
        + urllib.parse.quote_plus(sys.argv[2]) + "@127.0.0.1:27017/protect?authSource=admin"
mongo = PyMongo(app)

def generate_token(user_id):
    token = jwt.encode({'user_id': str(user_id), 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'])
    #return token.decode('UTF-8')
    return token

@app.route('/validate', methods=['POST'])
def validate_token():
    req = request.get_json()
    try:
        data = jwt.decode(req['token'], app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['user_id']
    except:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    user = {
        'email': data['email'],
        'password': hashed_password
    }
    existing_user = mongodb.users.find_one({'email': data['email']})
    if existing_user:
        return jsonify({'message': 'User already registered'}), 409
    mongo.db.users.insert_one(user)
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({'email': data['email']})
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        token = generate_token(user['_id'])
        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    from waitress import serve
    app.run(use_reloader=True, port=7778, threaded=True)

