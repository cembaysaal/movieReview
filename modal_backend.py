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
        
    @web_app.post("/user/contact")
    @jwt_required()
    def user_contact():

        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "user":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            data = request.get_json()
            name = data["name"]
            surname = data["surname"]
            email = data["email"]
            message = data["message"]

            if name == "" or email == "" or message == "":
                return jsonify({"message": "Please fill all the fields"}), 400

            db.child("user_messages").push({
                "name": name,
                "surname": surname,
                "email": email,
                "message": message
            })

            return jsonify({"message": "Message sent successfully"}), 200

        except Exception as e:
            return f"An Error Occured: {e}"
        
    @web_app.get("/user/movie/<string:id>")
    @jwt_required()
    def user_movie(id):

        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "user":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            movie = db.child("movies").child(id).get()
            return jsonify(movie.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"

    @web_app.post("/user/movie/<string:id>/create-comment")
    @jwt_required()
    def user_movie_comment(id):

        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "user":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            data = request.get_json()
            comment = data["comment"]
            name = data["name"]
            surname = data["surname"]

            if comment == "" or name == "" or surname == "":
                return jsonify({"message": "Please fill all the fields"}), 400

            db.child("movies").child(id).child("comments").push({
                "comment": comment,
                "name": name,
                "surname": surname
            })

            return jsonify({"message": "Comment added successfully"}), 200

        except Exception as e:
            return f"An Error Occured: {e}"

    @web_app.get("/user/movie/<string:id>/comments")
    @jwt_required()
    def user_movie_comments(id):
        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "user":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            comments = db.child("movies").child(id).child("comments").get()
            return jsonify(comments.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"

    @web_app.post("/user/movie/<string:movie_id>/add-star")
    @jwt_required()
    def user_add_star(movie_id):
        print("Route hit for movie_id:", movie_id)
        try:
            try:
                jwt_identity = get_jwt_identity()
                user_type = jwt_identity['type']

                if user_type != "user":
                    return jsonify({"message": "Invalid token"}), 400

            except:
                return jsonify({"message": "Invalid token"}), 400

            data = request.get_json()
            new_star_rating = data.get("star_rating")

            if new_star_rating is None:
                return jsonify({"message": "Please provide a star rating"}), 400
            if not 0 <= new_star_rating <= 5:
                return jsonify({"message": "Star rating must be between 0 and 5"}), 400

            movie_ref = db.child("movies").child(movie_id)
            movie = movie_ref.get()
            if not movie.val():
                return jsonify({"message": "Movie not found"}), 404

            rating_count = movie.val().get("rating_count")
            if (rating_count is None) or (rating_count == 0):
                rating_count = 1
            else:
                rating_count = rating_count + 1

            db.child("movies").child(movie_id).update(
                {"rating_count": rating_count})

            average_rating = db.child("movies").child(
                movie_id).child("average_rating").get().val()

            if (average_rating is None) or (average_rating == 0):
                average_rating = new_star_rating
            else:
                average_rating = (
                    average_rating * (rating_count - 1) + new_star_rating) / rating_count

            db.child("movies").child(movie_id).update(
                {"average_rating": average_rating})
            return jsonify({"message": "Star rating added successfully", "new_average_rating": average_rating}), 200

        except Exception as e:
            return jsonify({"message": f"An Error Occurred: {e}"}), 500

        
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
        
    @web_app.get("/admin/messages")
    @jwt_required()
    def admin_see_messages():

        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "admin":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            messages = db.child("user_messages").get()
            return jsonify(messages.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"
            
    @web_app.get("/admin/all-movies")
    @jwt_required()
    def admin_all_movies():
        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "admin":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            movies = db.child("movies").get()
            return jsonify(movies.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"
        
    @web_app.get("/admin/get-users")
    @jwt_required()
    def admin_get_users():
        try:
            jwt_identity = get_jwt_identity()
            user_type = jwt_identity['type']

            if user_type != "admin":
                return jsonify({"message": "Invalid token"}), 400
        except:
            return jsonify({"message": "Invalid token"}), 400

        try:
            users = db.child("users").get()
            return jsonify(users.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"
        

    @web_app.post("/admin/add-movie")
    @jwt_required()
    def admin_add_movie():

        movie_name = ""
        year = ""
        photo_url = ""
        duration = ""
        story_line = ""

        try:
            try:
                jwt_identity = get_jwt_identity()
                user_type = jwt_identity['type']

                if user_type != "admin":
                    return jsonify({"message": "Invalid token"}), 400
            except:
                return jsonify({"message": "Invalid token"}), 400

            data = request.get_json()
            movie_name = data.get("movieName")
            year = data.get("year")
            photo_url = data.get("photoLink")
            duration = data.get("duration")
            story_line = data.get("storyline")

            if movie_name == "" or year == "" or photo_url == "" or duration == "" or story_line == "":
                return jsonify({"message": "Please fill all the fields"}), 400

            try:
                duration = int(duration)

            except:
                return jsonify({"message": "Duration must be integer"}), 400

            movie_data = {
                "movie_name": movie_name,
                "movie_year": year,
                "movie_image_link": photo_url,
                "movie_duration": duration,
                "movie_story_line": story_line,
                "average_rating": 0,
                "rating_count": 0
            }

            db.child("movies").push(movie_data)

            return jsonify({"message": "movie added successfully"}), 201

        except Exception as e:
            return jsonify({"message": f"An Error Occurred: {e}"}), 500

        
########################################################################################################################################################################
#                                                                       GUEST ROUTES                                                                                   #
########################################################################################################################################################################  
        
    @web_app.get("/guest/all-movies")
    def guest_all_movies():
        try:
            movies = db.child("movies").get()
            return jsonify(movies.val()), 200
        except Exception as e:
            return f"An Error Occured: {e}"
    
########################################################################################################################################################################
#                                                             EXTERNAL API CONFIGURATION                                                                               #
########################################################################################################################################################################    
    def get_weather(city, country_code):
        api_key = "3536a7b4d62e6be4384cefacde2034c8"
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        complete_url = f"{base_url}?q={city},{country_code}&appid={api_key}&units=metric"

        response = requests.get(complete_url)
        return response.json()
    
    
    @web_app.post("/weather")
    def weather():
        data = request.get_json()
        city = data.get('city')
        country_code = data.get('country_code')

        if not city or not country_code:
            return jsonify({"error": "Missing city or country code"}), 400

        weather_data = get_weather(city, country_code)
        return jsonify(weather_data)

        


    return web_app
