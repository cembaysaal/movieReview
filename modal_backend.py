import pyrebase
from modal import Stub, wsgi_app, Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import  create_access_token, JWTManager, jwt_required, get_jwt_identity
import secrets
import time
import requests

########################################################################################################################################################################
#                                                                 DATABASE & APP CONFIGURATION                                                                         #
########################################################################################################################################################################
firebaseConfig = {
    "apiKey": "AIzaSyC5XPTzg-N-gQZEYt1hgNyadIi68cyaByM",
    "authDomain": "web-proje-ece1f.firebaseapp.com",
    "databaseURL": "https://web-proje-ece1f-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "web-proje-ece1f",
    "storageBucket": "web-proje-ece1f.appspot.com",
    "messagingSenderId": "684207171527",
    "appId": "1:684207171527:web:9356621e2bb8eea7d69be2",
    "measurementId": "G-NGNHNDV64R"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

########################################################################################################################################################################
#                                                                       App Configuration                                                                              #
########################################################################################################################################################################

stub = Stub("web-group-project",
             image=Image.debian_slim().pip_install("flask-cors","Flask-JWT-Extended","Flask-Cors","flask", "pyrebase4", "python-dotenv", "python-jose[cryptography]"),
)

      
@stub.function()
@wsgi_app()
def flask_app():
    web_app = Flask(__name__)
    jwt = JWTManager(web_app)
    CORS(web_app, supports_credentials=True)
    secret_key = secrets.token_urlsafe(32)
    web_app.config["JWT_SECRET_KEY"] = secret_key


########################################################################################################################################################################
#                                                                        USER ROUTES                                                                                   #
########################################################################################################################################################################

    @web_app.post("/user/register")
    def user_register():
        name = ""
        surname = ""
        email = ""
        password = ""

        try:
            data = request.get_json()
            name = data["name"]
            surname = data["surname"]
            email = data["email"]
            password = data["password"]

            if name == "" or surname == "" or email == "" or password == "":
                return jsonify({"message": "Please fill all the fields"}), 400

            users = db.child("users").get()
            for user in users.each():
                if user.val()['email'] == email:
                    return jsonify({"message": "User with this email already exists"}), 400

            if len(password) < 6:
                return jsonify({"message": "Password must contain at least 6 characters"}), 400

            if not any(char.isdigit() for char in password):
                return jsonify({"message": "Password must contain at least one number"}), 400

            if not any(char.isupper() for char in password):
                return jsonify({"message": "Password must contain at least one uppercase letter"}), 400

            db.child("users").push({
                "name": name,
                "surname": surname,
                "email": email,
                "password": password
            })

            return jsonify({"message": "User registered successfully"}), 200
        except Exception as e:
            return f"An Error Occured: {e}"
        
        
    @web_app.post("/user/login")
    def user_login():
        email = ""
        password = ""

        try:
            data = request.get_json()
            email = data["email"]
            password = data["password"]

            if email == "" or password == "":
                return jsonify({"message": "Please fill all the fields"}), 400

            users = db.child("users").get()
            for user in users.each():
                if user.val()['email'] == email and user.val()['password'] == password:
                    access_token = create_access_token(
                        identity={"type": "user", "id": user.key()})
                    user_name = user.val().get('name')
                    user_surname = user.val().get('surname')
                    print(user_name)
                    print(user_surname)
                    return jsonify({
                        "message": "User logged in successfully",
                        "access_token": access_token,
                        "name": user_name,
                        "surname": user_surname
                    }), 200

            return jsonify({"message": "User with this email does not exist"}), 400
        except Exception as e:
            return f"An Error Occured: {e}"
        
        
    @web_app.get("/user/all-movies")
    @jwt_required()
    def user_all_movies():
        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "user":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            movies = db.child("movies").get()
            return jsonify(movies.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"
        
        
########################################################################################################################################################################
#                                                                       ADMIN ROUTES                                                                                   #
########################################################################################################################################################################    
    @web_app.post("/admin/login")
    def admin_login():
        email = ""
        password = ""

        try:
            data = request.get_json()
            email = data["email"]
            password = data["password"]

            if email == "" or password == "":
                return jsonify({"message": "Please fill all the fields"}), 400

            admins = db.child("admin").get()

            for admin in admins.each():
                if admin.val()['email'] == email and admin.val()['password'] == password:
                    access_token = create_access_token(
                        identity={"type": "admin", "id": admin.key()})
                    return jsonify({"message": "Admin logged in successfully", "access_token": access_token}), 200
        except:
            return jsonify({"message": "Admin with this email does not exist"}), 400
    
    return web_app