from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import json_util
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_cors import CORS
import smtplib, ssl
import os
import sys
import urllib
import json
import random
import string
import time

app = Flask(__name__)  # Flask server
CORS(app)

client = MongoClient()  # Create client object

load_dotenv()  # Load environment variables

mongouri = "mongodb://" + urllib.parse.quote_plus(sys.argv[1]) + ":"\
        + urllib.parse.quote_plus(sys.argv[2]) + "@127.0.0.1:27017/"
client = MongoClient(mongouri)  # Client makes connection

db = client['protect']  # Select database

@app.route('/app/info_student', methods=['POST'])
def app_info_student():
    matricula = request.get_json()
    matricula = matricula["matricula"]
    student_info = db.students.find_one({"matricula": matricula})
    student_info = json.loads(json_util.dumps(student_info))
    return student_info

@app.route('/dashboard/update', methods=['POST'])
def dasbboard_update():
    new_student_data = request.get_json()
    matricula = new_student_data["matricula"]
    update_student = db.students.update_one({"matricula": matricula}, {"$set": new_student_data})
    return jsonify({"status": "Data updated"})

@app.route('/dashboard/upload', methods=['POST'])
def dashboard_upload():
    info = request.get_json()
    section = info["section"]
    info.pop("section")
    if section == "register":
        add_student = db.students.insert_one(info)
    elif section == "safe":
        add_safe = db.safe.insert_one(info)
    elif section == "emergency":
        add_emergency = db.emergency.insert_one(info)
    else:
        return jsonify({"status": "No section"})
    return jsonify({"status": "Data uploaded"})

@app.route('/dashboard/safe/info', methods=['GET'])
def dashboard_safe_info():
    safe_students = db.safe.find()
    safe_students = json.loads(json_util.dumps(safe_students))
    return safe_students

@app.route('/dashboard/emergency/info', methods=['GET'])
def dashboard_emergency_info():
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
