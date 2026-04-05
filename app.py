from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import base64
import numpy as np
from datetime import datetime


app = Flask(__name__)
CORS(app)

# ---------------- STORAGE ----------------
users = {}
history = {}

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    username = data.get('username')
    password = data.get('password')

    # Empty check
    if not username or not password:
        return jsonify({"status": "error", "message": "Enter username & password"})

    # 🆕 NEW USER → CREATE ACCOUNT
    if username not in users:
        users[username] = password
        history[username] = []
        return jsonify({
            "status": "created",
            "message": "Account created! Logged in"
        })

    # 🔐 EXISTING USER → CHECK PASSWORD
    if users[username] == password:
        return jsonify({
            "status": "success",
            "message": "Login successful"
        })

    # ❌ WRONG PASSWORD
    return jsonify({
        "status": "error",
        "message": "Wrong password"
    })

# ---------------- SCAN ----------------
@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No data"}), 400

        image_data = data.get('image')
        username = data.get('username')

        if not image_data or not username:
            return jsonify({"error": "Missing data"}), 400

        # Decode image
        img_bytes = base64.b64decode(image_data.split(',')[1])
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # -------- SIMPLE SMART LOGIC --------
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        avg = np.mean(gray)

        conditions = []
        suggestions = []

        if avg < 85:
            conditions.append("Dry Skin")
            suggestions.append("Moisturizer + Hyaluronic Acid")

        if avg > 170:
            conditions.append("Oily Skin")
            suggestions.append("Oil-free Cleanser + Niacinamide")

        if 100 < avg < 150:
            conditions.append("Acne")
            suggestions.append("Salicylic Acid / Benzoyl Peroxide")

        if avg < 70:
            conditions.append("Eczema")
            suggestions.append("Thick Moisturizer + Gentle Cleanser")

        if avg > 190:
            conditions.append("Sunburn")
            suggestions.append("Aloe Vera Gel + Sunscreen")

        if 120 < avg < 160:
            conditions.append("Dermatitis")
            suggestions.append("Soothing Lotion")

        # If nothing detected
        if len(conditions) == 0:
            conditions = ["Normal Skin"]
            suggestions = ["Basic Routine: Cleanser + Moisturizer + Sunscreen"]

        # Limit to 3
        conditions = conditions[:3]
        suggestions = suggestions[:3]

        # -------- SAVE HISTORY --------
        if username not in history:
            history[username] = []

            score = max(0, 100 - len(conditions)*20)

        history[username].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "condition": conditions[0]
        })

        return jsonify({
    "conditions": conditions,
    "suggestions": suggestions,
    "score": max(0, 100 - len(conditions)*20),
    "warning": "Consult dermatologist if severe"
})
        
    except Exception as e:
        return jsonify({"error": str(e)})
    

    # ---------------- FACE CHECK ----------------
@app.route('/check_face', methods=['POST'])
def check_face():
    try:
        data = request.json
        image_data = data.get('image')

        if not image_data:
            return jsonify({"status": "no_face"})

        # Decode image
        img_bytes = base64.b64decode(image_data.split(',')[1])
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return jsonify({"status": "no_face"})

        x, y, w, h = faces[0]
        h_img, w_img = gray.shape

        center_x = x + w/2
        center_y = y + h/2

        # 🔥 POSITION CHECK
        pos = "center"

        if center_x < w_img * 0.3:
            pos = "left"
        elif center_x > w_img * 0.7:
            pos = "right"
        elif center_y < h_img * 0.3:
            pos = "up"
        elif center_y > h_img * 0.7:
            pos = "down"

        # 🔥 SIZE CHECK (distance)
        face_area = w * h
        img_area = w_img * h_img
        ratio = face_area / img_area

        if ratio < 0.1:
            distance = "far"
        elif ratio > 0.4:
            distance = "close"
        else:
            distance = "good"

        # 🔥 FINAL DECISION
        if pos == "center" and distance == "good":
            return jsonify({"status": "perfect"})
        else:
            return jsonify({
                "status": "adjust",
                "position": pos,
                "distance": distance
            })

    except Exception as e:
        print("Face check error:", e)
        return jsonify({"status": "error"})


# ---------------- HISTORY ----------------
@app.route('/history/<username>', methods=['GET'])
def get_history(username):
    return jsonify(history.get(username, []))

@app.route('/')
def home():
    return "Skin AI Backend is running 🚀"


# ---------------- RUN ----------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
