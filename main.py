from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import json_util
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import smtplib, ssl
import os
import sys
import urllib
import json
import random
import string
import time
import jwt

app = Flask(__name__)  # Flask server
CORS(app)

client = MongoClient()  # Create client object

load_dotenv()  # Load environment variables

secret_key = os.getenv('SECRETKEY')

app.config['SECRET_KEY'] = secret_key

mongouri = "mongodb://" + urllib.parse.quote_plus(sys.argv[1]) + ":"\
        + urllib.parse.quote_plus(sys.argv[2]) + "@127.0.0.1:27017/"
client = MongoClient(mongouri)  # Client makes connection

db = client['protect']  # Select database

def getTime():
    today = datetime.now()
    d1 = today.strftime("%d/%m/%Y %H:%M:%S")
    return d1

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = db.users.find_one({'_id': ObjectId(data['user_id'])})
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def pin_required(f):
    pin = secret_key

    if f != pin:
        return False
    elif f == pin:
        return True

@app.route('/app/info_student', methods=['POST'])
def app_info_student():
    email = request.get_json()
    PIN = email["PIN"]
    if pin_required(PIN):
        email = email["email"]
        student_info = db.students.find_one({"email": email})
        student_info = json.loads(json_util.dumps(student_info))
        return student_info
    else:
        return jsonify({"status": "Invalid or missing PIN"}), 401

@app.route('/app/update', methods=['POST'])
def dashboard_update():
    new_student_data = request.get_json()
    PIN = new_student_data["PIN"]
    if pin_required(PIN):
        new_student_data.pop("PIN")
        email = new_student_data["email"]
        check_if_registered = db.students.find_one({"email": email})
        if check_if_registered:
            update_student = db.students.update_one({"email": email}, {"$set": new_student_data})
            return jsonify({"status": "Data updated"})
        else:
            update_student = db.students.insert_one(new_student_data)
            return jsonify({"status": "Student registered"})
    else:
        return jsonify({"status": "Invalid or missing PIN"}), 401

@app.route('/dashboard/upload', methods=['POST'])
def dashboard_upload():
    info = request.get_json()
    email = info["email"]
    section = info["section"]
    PIN = info["PIN"]
    new_info = db.students.find_one({"email": email})
    new_info["latitud"] = info["latitud"]
    new_info["longitud"] = info["longitud"]
    new_info.pop("_id")
    if pin_required(PIN):
        if section == "safe":
            new_info["fecha"] = getTime()
            add_safe = db.safe.insert_one(new_info)
        elif section == "emergency":
            new_info["fecha"] = getTime()
            add_emergency = db.emergency.insert_one(new_info)
        else:
            return jsonify({"status": "No section"})
        return jsonify({"status": "Data uploaded"})
    else:
        return jsonify({"status": "Invalid or missing PIN"}), 401

@app.route('/dashboard/safe/coordinates', methods=['GET'])
@token_required
def dashboard_safe_coordinates(current_user):
    pipeline = [
        {
            "$project": {
                "lat": "$latitud",
                "lng": "$longitud",
                "_id": 0
            }
        }
    ]
    coordinates = list(db.safe.aggregate(pipeline))
    return coordinates

@app.route('/dashboard/emergency/coordinates', methods=['GET'])
@token_required
def dashboard_emergency_coordinates(current_user):
    pipeline = [
        {
            "$project": {
                "lat": "$latitud",
                "lng": "$longitud",
                "_id": 0
            }
        }
    ]
    coordinates = list(db.emergency.aggregate(pipeline))
    return coordinates

@app.route('/dashboard/safe/info', methods=['GET'])
@token_required
def dashboard_safe_info(current_user):
    safe_students = db.safe.find()
    safe_students = json.loads(json_util.dumps(safe_students))
    return safe_students

@app.route('/dashboard/emergency/info', methods=['GET'])
@token_required
def dashboard_emergency_info(current_user):
    emergency_students = db.emergency.find()
    emergency_students = json.loads(json_util.dumps(emergency_students))
    return emergency_students

if __name__ == '__main__':
    from waitress import serve
    # For local testing
    app.run(use_reloader=True, port=7777, threaded=True)
    # For deployment
    #tl.start()
    #serve(app, host="0.0.0.0", port=5000, url_scheme='https')
