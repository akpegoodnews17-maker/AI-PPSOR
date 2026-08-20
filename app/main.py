from flask import Flask, render_template, current_app, request, jsonify, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from app.finder import FashionFinder
from functools import wraps
#import from app.database import DatabaseInitializer
#from ai_engine.fashion_recommender import recommend_fashion
#from ai_engine.virtual_try_on import run_virtual_try_on
#from ai_engine.age_gender_skinTone import process_fashion_recommendation
#from celery_setup import celery
import os
try:
    import google.generativeai as ai
except ImportError:
    ai = None
import logging
import atexit
import time
import json
import asyncio
from threading import Thread
import requests
from flask import Flask, render_template, current_app, request, jsonify, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, date
from werkzeug.utils import secure_filename
from app.globals import season as global_season

# Directory to save the images
PROFILE_PIC_FOLDER = 'app/static/uploads/profile/'
WARDROBE_IMG_FOLDER = 'app/static/uploads/wardrobe/'
VIRTUAL_TRY_ON_IMG_FOLDER = os.path.join('app/static/uploads/virtual_try_on/')

os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)
os.makedirs(WARDROBE_IMG_FOLDER, exist_ok=True)
os.makedirs(VIRTUAL_TRY_ON_IMG_FOLDER, exist_ok=True)

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"
logging.getLogger('google.generativeai').setLevel(logging.CRITICAL)
logging.getLogger('grpc').setLevel(logging.CRITICAL)

API_KEY = os.getenv('G_API_KEY')
chat = None
if ai is not None and API_KEY:
    try:
        ai.configure(api_key=API_KEY)
        model = ai.GenerativeModel("gemini-1.5-pro-latest")
        chat = model.start_chat()
    except Exception as e:
        logging.warning(f"Could not configure Gemini API: {e}")
else:
    logging.warning("G_API_KEY and/or google-generativeai package is not available; Gemini chat will run in fallback mode.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'manojrajgopal'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fashion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Session configuration for persistent login
app.config['PERMANENT_SESSION_LIFETIME'] = 365 * 24 * 3600  # 1 year
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)

def initialize_local_database():
    with app.app_context():
        db.session.execute(text("PRAGMA foreign_keys = ON"))
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                phone TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """))
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                profile_pic TEXT,
                gender TEXT,
                date_of_birth DATE,
                body_type TEXT,
                height REAL,
                weight REAL,
                preferred_color TEXT,
                preferred_fabrics TEXT,
                preferred_styles TEXT,
                occasion_types TEXT,
                style_goals TEXT,
                budget REAL,
                skin_color TEXT,
                wardrobe_img TEXT,
                user_title TEXT,
                user_about_1 TEXT,
                user_about_2 TEXT,
                virtual_try_on_image TEXT,
                FOREIGN KEY (username) REFERENCES login(username) ON DELETE CASCADE
            )
        """))
        db.session.commit()

initialize_local_database()

def login_required(f):
    """Decorator to protect routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        # Make session permanent on each request
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

class Dashboard:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        # Define the route for the main dashboard page
        self.app.add_url_rule('/', view_func=self.main, methods=['GET', 'POST'])
        self.app.add_url_rule('/main-feature-recommendation', view_func=self.main_feature_recommendation, methods=['POST'])

    def _map_weather_api_to_bucket(self, weather_payload):
        weather_main = ""
        temperature = None
        if weather_payload:
            weather = weather_payload.get("weather", [])
            if weather:
                weather_main = (weather[0].get("main") or "").lower()
            temperature = weather_payload.get("main", {}).get("temp")

        if weather_main in {"rain", "drizzle", "thunderstorm"}:
            return "Rainy"
        if isinstance(temperature, (int, float)):
            if temperature >= 27:
                return "Hot"
            if temperature <= 16:
                return "Cold"
        return None

    def _get_weather_bucket(self, selected_weather, city):
        selected = (selected_weather or "").title()
        if selected in {"Hot", "Rainy", "Cold"}:
            fallback_weather = selected
        else:
            fallback_weather = "Hot"

        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not city or not api_key:
            return fallback_weather, "simulated"

        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": api_key, "units": "metric"}
            weather_payload = requests.get(url, params=params, timeout=6).json()
            bucket = self._map_weather_api_to_bucket(weather_payload)
            if bucket:
                return bucket, "openweathermap"
        except Exception as e:
            print(f"Weather API fallback activated: {e}")

        return fallback_weather, "simulated"

    def _build_main_feature_payload(self, occasion, weather_bucket, style_note, uploaded_image):
        occasion_outfits = {
            "Casual": ["White relaxed tee", "Blue straight jeans", "Clean white sneakers"],
            "Office": ["Oxford shirt", "Tailored trousers", "Leather loafers"],
            "Party": ["Statement blazer", "Dark slim pants", "Chelsea boots"],
            "Date": ["Soft knit top", "Well-fitted chinos/skirt", "Minimal sneakers or heels"]
        }

        weather_advice = {
            "Hot": [
                "Choose breathable cotton or linen pieces.",
                "Prefer lighter tones to stay cooler under sun.",
                "Keep layers minimal and use open footwear when possible."
            ],
            "Rainy": [
                "Avoid suede shoes and heavy absorbent fabrics.",
                "Use quick-dry outer layers and water-resistant footwear.",
                "Carry a compact jacket in case showers start."
            ],
            "Cold": [
                "Build with layers: thermal base, knit mid-layer, warm outer shell.",
                "Use wool blends and closed shoes for insulation.",
                "Add scarf/beanie accessories for functional style."
            ]
        }

        style_lower = (style_note or "").lower()
        style_recommendations = [
            "These two items pair well: white shirt + navy bottoms.",
            "Balance one statement piece with neutral basics."
        ]

        if "black" in style_lower:
            style_recommendations.insert(0, "You wear black a lot, try lighter tones like cream, beige, or soft blue.")
        if "formal" in style_lower:
            style_recommendations.append("To soften formal looks, mix in one casual texture like denim or knit.")
        if "minimal" in style_lower:
            style_recommendations.append("Monochrome plus one contrasting accessory keeps minimal looks sharp.")

        outfit_items = occasion_outfits.get(occasion, occasion_outfits["Casual"])
        pairings = [
            f"{outfit_items[0]} + {outfit_items[1]}",
            f"{outfit_items[1]} + {outfit_items[2]}"
        ]

        gallery_items = self._build_gallery_items(occasion, weather_bucket)
        inspiration_photos = self._fetch_inspiration_photos(occasion, weather_bucket, style_note)

        mannequin_rel_path = 'images/profile/male-avatar.png'
        if occasion in {"Party", "Date"}:
            mannequin_rel_path = 'images/profile/female-avatar.png'
        mannequin_image = url_for('static', filename=mannequin_rel_path)
        mannequin_fs_path = os.path.join('app', 'static', mannequin_rel_path.replace('/', os.sep))

        uploaded_preview = None
        overlay_preview = None
        if uploaded_image and uploaded_image.filename:
            upload_name = f"preview_{int(time.time())}_{secure_filename(uploaded_image.filename)}"
            upload_path = os.path.join(VIRTUAL_TRY_ON_IMG_FOLDER, upload_name)
            uploaded_image.save(upload_path)
            uploaded_preview = url_for('static', filename=f'uploads/virtual_try_on/{upload_name}')
            overlay_preview = self._create_simple_overlay(upload_path, mannequin_fs_path)

        return {
            "occasion": occasion,
            "weather": weather_bucket,
            "weather_suggestions": weather_advice.get(weather_bucket, weather_advice["Hot"]),
            "recommended_outfit": outfit_items,
            "style_recommendations": style_recommendations,
            "pairings": pairings,
            "gallery_items": gallery_items,
            "inspiration_photos": inspiration_photos,
            "virtual_try_on": {
                "simple_mode": {
                    "title": "Mannequin Preview",
                    "image": mannequin_image,
                    "note": "Simple mode shows your outfit direction on an avatar/mannequin."
                },
                "advanced_mode": {
                    "enabled": bool(uploaded_preview),
                    "overlay_preview": overlay_preview or uploaded_preview,
                    "note": "Advanced mode uses your uploaded image as an overlay preview."
                }
            }
        }

    def _usd_to_ngn(self, amount_usd):
        conversion_rate = 1600
        return int(round(float(amount_usd) * conversion_rate))

    def _build_gallery_items(self, occasion, weather_bucket):
        products_by_occasion = {
            "Casual": [
                {"title": "Relaxed Cotton Shirt", "image": "images/products/shirt-1.jpg", "price_usd": 18.99, "tag": "Easy Daywear"},
                {"title": "Denim Friendly Jacket", "image": "images/products/jacket-2.jpg", "price_usd": 34.00, "tag": "Street Casual"},
                {"title": "Clean White Sneaker", "image": "images/products/sports-1.jpg", "price_usd": 29.50, "tag": "Everyday Step"}
            ],
            "Office": [
                {"title": "Crisp Work Shirt", "image": "images/products/shirt-2.jpg", "price_usd": 24.99, "tag": "Office Sharp"},
                {"title": "Tailored Formal Shoes", "image": "images/products/shoe-1.jpg", "price_usd": 49.00, "tag": "Boardroom Ready"},
                {"title": "Minimal Leather Watch", "image": "images/products/watch-1.jpg", "price_usd": 39.99, "tag": "Executive Finish"}
            ],
            "Party": [
                {"title": "Statement Party Heels", "image": "images/products/party-wear-1.jpg", "price_usd": 42.00, "tag": "Night Energy"},
                {"title": "Bold Party Shoes", "image": "images/products/party-wear-2.jpg", "price_usd": 44.50, "tag": "Spotlight Piece"},
                {"title": "Layered Party Jacket", "image": "images/products/jacket-5.jpg", "price_usd": 55.00, "tag": "After-Hours Look"}
            ],
            "Date": [
                {"title": "Soft Date-Night Dress", "image": "images/products/clothes-3.jpg", "price_usd": 31.00, "tag": "Romantic Tone"},
                {"title": "Fine-Strap Watch", "image": "images/products/watch-3.jpg", "price_usd": 36.50, "tag": "Polished Detail"},
                {"title": "Confident Date Shoes", "image": "images/products/shoe-2.jpg", "price_usd": 46.00, "tag": "Evening Walk"}
            ]
        }

        weather_image_boost = {
            "Hot": "images/products/shorts-1.jpg",
            "Rainy": "images/products/jacket-1.jpg",
            "Cold": "images/products/jacket-6.jpg"
        }

        selected_items = products_by_occasion.get(occasion, products_by_occasion["Casual"])
        cards = []
        for item in selected_items:
            cards.append({
                "title": item["title"],
                "tag": item["tag"],
                "image": url_for("static", filename=item["image"]),
                "price_usd": item["price_usd"],
                "price_ngn": self._usd_to_ngn(item["price_usd"])
            })

        cards.append({
            "title": f"{weather_bucket} Weather Essential",
            "tag": "Weather Pick",
            "image": url_for("static", filename=weather_image_boost.get(weather_bucket, "images/products/shorts-1.jpg")),
            "price_usd": 27.99,
            "price_ngn": self._usd_to_ngn(27.99)
        })

        return cards

    def _fetch_inspiration_photos(self, occasion, weather_bucket, style_note):
        finder = FashionFinder()
        if not finder.api_key or not finder.cx:
            return []

        query = f"{occasion} outfit for {weather_bucket} weather"
        filters = [style_note] if style_note else []

        try:
            search_items = finder.search_google_api(query=query, filters=filters, num_results=6)
        except Exception:
            return []

        photos = []
        for item in search_items[:4]:
            image_link = item.get("image") or item.get("link")
            if not image_link:
                continue
            photos.append({
                "title": item.get("title") or "Outfit inspiration",
                "image": image_link,
                "source": "web"
            })

        return photos

    def _create_simple_overlay(self, user_image_path, mannequin_path):
        try:
            from PIL import Image

            if not os.path.exists(user_image_path) or not os.path.exists(mannequin_path):
                return None

            user_img = Image.open(user_image_path).convert("RGBA")
            mannequin_img = Image.open(mannequin_path).convert("RGBA")

            width, height = user_img.size
            mannequin_img = mannequin_img.resize((width, height))

            # Keep user image visible while placing a styling silhouette on top.
            mannequin_img.putalpha(95)
            blended = Image.alpha_composite(user_img, mannequin_img)

            output_name = f"overlay_{int(time.time())}_{os.path.basename(user_image_path)}.png"
            output_path = os.path.join(VIRTUAL_TRY_ON_IMG_FOLDER, output_name)
            blended.convert("RGB").save(output_path)
            return url_for('static', filename=f'uploads/virtual_try_on/{output_name}')
        except Exception as e:
            print(f"Overlay generation failed: {e}")
            return None

    def main_feature_recommendation(self):
        try:
            occasion = (request.form.get('occasion') or '').title()
            weather = (request.form.get('weather') or '').title()
            city = (request.form.get('city') or '').strip()
            style_note = (request.form.get('style_note') or '').strip()
            uploaded_image = request.files.get('user_image')

            if occasion not in {"Casual", "Office", "Party", "Date"}:
                return jsonify({"error": "Invalid occasion selected."}), 400

            if not weather or weather not in {"Hot", "Rainy", "Cold"}:
                return jsonify({"error": "Invalid weather selected."}), 400

            weather_bucket, weather_source = self._get_weather_bucket(weather, city)
            payload = self._build_main_feature_payload(occasion, weather_bucket, style_note, uploaded_image)
            payload["weather_source"] = weather_source
            payload["city"] = city or "Not provided"

            return jsonify(payload)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def main(self):
        if request.method == "POST":
            # Handle form submission for email subscription
            email = request.form.get("email")
            if email:
                print(f"New subscription: {email}")
        # Render the main dashboard page
        return render_template('index.html', title='Outfit Recommender')

class Login:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.register_routes()

    def register_routes(self):
        # Define routes for login, signup, and logout
        self.app.add_url_rule('/login', methods=['GET', 'POST'], view_func=self.login)
        self.app.add_url_rule('/signup', methods=['POST'], view_func=self.signup)
        self.app.add_url_rule('/logout', methods=['GET'], view_func=self.logout)
        self.app.add_url_rule('/get_location', methods=['POST'], view_func=self.get_location)  # ✅ Add this

    def get_location(self):
        data = request.get_json()
        lat, lon = data.get('latitude'), data.get('longitude')

        if lat is None or lon is None:
            return jsonify({"error": "Latitude and longitude are required"}), 400

        try:
            api_key = (os.getenv("OPENWEATHERMAP_API_KEY") or "").strip()
            if not api_key:
                return jsonify({"error": "OpenWeatherMap API key is not configured."}), 500

            geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
            geo_response = requests.get(geo_url, timeout=10).json()

            city = geo_response[0]["name"] if geo_response and len(geo_response) > 0 else "Unknown City"

            month = datetime.now().month
            if lat >= 0:
                season = ["Winter", "Spring", "Summer", "Fall"][(month % 12) // 3]
            else:
                season = ["Summer", "Fall", "Winter", "Spring"][(month % 12) // 3]

            from app import globals
            globals.season = season
            return jsonify({"city": city, "season": season})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_location_manual(self, lat, lon):
        try:
            api_key = (os.getenv("OPENWEATHERMAP_API_KEY") or "").strip()
            if not api_key:
                return {"city": "Unknown City", "season": "Unknown Season", "error": "OpenWeatherMap API key is not configured."}

            geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
            geo_response = requests.get(geo_url, timeout=10).json()

            city = geo_response[0]["name"] if geo_response and len(geo_response) > 0 else "Unknown City"

            month = datetime.now().month
            if lat >= 0:
                season = ["Winter", "Spring", "Summer", "Fall"][(month % 12) // 3]
            else:
                season = ["Summer", "Fall", "Winter", "Spring"][(month % 12) // 3]

            from app import globals
            globals.season = season
            return {"city": city, "season": season}

        except Exception as e:
            return {"city": "Unknown City", "season": "Unknown Season", "error": str(e)}

    def login(self):
        if request.method == 'POST':
            # Get username and password from the login form
            username = request.form['username'].lower()
            password = request.form['password']

            # Safely execute the query to check login credentials
            query = text('SELECT username, email, phone, name, password FROM login WHERE username=:username AND password=:password')
            result = self.db.session.execute(query, {'username': username, 'password': password})
            user = result.fetchone()  # Fetch the first matching row
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')

            # Fetch city and season using get_location
            city = request.form.get('city', 'Unknown City')
            season = request.form.get('season', 'Unknown Season')

            if lat and lon:
                location_data = self.get_location_manual(float(lat), float(lon))  # Call a helper function
                city = location_data.get("city", "Unknown City")
                season = location_data.get("season", "Unknown Season")

            if user:
                # Make session permanent
                session.permanent = True
                # Store user information in the session
                session['user'] = {'username': user[0], 'email': user[1], 'phone': user[2], 'name': user[3], 'password': password, 'city':city}  # username = user[0], email = user[1], phone = user[2]
            
                # Now check if the user exists in the user_information table
                query_user_info = text('SELECT username FROM user_information WHERE username=:username')
                result_user_info = self.db.session.execute(query_user_info, {'username': username})
                user_info = result_user_info.fetchone()
                session['user']['city'] = city
                session['user']['season'] = season
                if not user_info:
                    # If user is not in user_information table, redirect to the quiz page
                    return redirect(url_for('quiz', name=session['user']['name'], username=session['user']['username'], phone=session['user']['phone'], email=session['user']['email']))
                else:
                    # If user exists in user_information table, redirect to the main page
                    return redirect(url_for('main'))  # Or your main dashboard page

            else:
                # If username or password is incorrect
                return render_template('login.html', message="Invalid username or password")

        # Render login page if the request method is GET
        return render_template('login.html', title='Fashion Hub')

    def signup(self):
        if request.method == 'POST':
            # Get user details from the signup form
            name = request.form['name'].title()
            username = request.form['username'].lower().strip().replace(" ", "")
            phone = request.form['phone']
            email = request.form['email'].lower()
            password = request.form['password']
            # Get latitude and longitude from the form (hidden fields from JavaScript)
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')

            # Fetch city and season using get_location
            city = request.form.get('city', 'Unknown City')
            season = request.form.get('season', 'Unknown Season')

            if lat and lon:
                location_data = self.get_location_manual(float(lat), float(lon))  # Call a helper function
                city = location_data.get("city", "Unknown City")
                season = location_data.get("season", "Unknown Season")

            # Check if the username already exists in the login table
            query_check_username = text('SELECT username FROM login WHERE username=:username')
            result = self.db.session.execute(query_check_username, {'username': username})
            existing_user = result.fetchone()

            if existing_user:
                return render_template('login.html', message="Username already exists. Please choose a different username.")

            # Store user details in the session for later use
            session['user_details'] = {
                'name': name,
                'username': username,
                'phone': phone,
                'email': email,
                'password': password,
                'city': city or "Unknown City",
                'season': season or "Unknown Season"
            }

            return render_template('quiz.html', name=session['user_details']['name'], username=session['user_details']['username'], phone=session['user_details']['phone'], email=session['user_details']['email'])
        return render_template('login.html', title='Sign Up')


    def logout(self):
        # Clear the session data and log out the user
        session.pop('user', None)
        session.permanent = False
        return redirect(url_for('login'))  # Redirect to the login page after logging out

class Profile:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.register_routes()

    def register_routes(self):
        # Profile route requires login
        self.app.add_url_rule('/profile', methods=['GET'], view_func=login_required(self.profile))
        self.app.add_url_rule('/quiz', methods=['GET', 'POST'], view_func=self.quiz)
        self.app.add_url_rule('/dataset-images/<path:filename>', methods=['GET'], view_func=self.dataset_images)
        # Virtual try-on requires login
        self.app.add_url_rule('/run_virtual_try_on', methods=['GET', 'POST'], view_func=login_required(self.virtual_try_on))
        self.app.add_url_rule('/check_status/<username>/<vton_img>/<garm_img>', methods=['GET', 'POST'], view_func=self.check_status)

    IMAGES_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "data", "fashion-dataset", "images"))
    def dataset_images(self, filename):
        IMAGES_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "data", "fashion-dataset", "images"))
        return send_from_directory(IMAGES_FOLDER, filename)
    
    def virtual_try_on(self):
        username = session.get('user', {}).get('username')
        if not username:
            return jsonify({"success": False, "error": "User not logged in."})

        data = request.json
          # Replace with dynamic path if needed
        img_name = db.session.execute(
                text("SELECT virtual_try_on_image FROM user_information WHERE username = :username"), 
                {"username": username}
            )
        vton_img_path = f"app/static/uploads/virtual_try_on/" + img_name.fetchone()[0]
        garm_img_path = data.get("garm_img_path").replace("/dataset-images", "data/fashion-dataset/images")

        try:
            from ai_engine.virtual_try_on import run_virtual_try_on
        except Exception as e:
            return jsonify({"success": False, "error": f"Virtual try-on import failed: {e}"})

        if not vton_img_path or not garm_img_path:
            return jsonify({"success": False, "error": "Image paths missing."})

        self.vton_img_name = os.path.splitext(os.path.basename(vton_img_path))[0].replace(" ", "_")
        garm_img_name = os.path.splitext(os.path.basename(garm_img_path))[0].replace(" ", "_")

        user_folder = os.path.normpath(os.path.join("app/static/virtual_try_on", username))
        os.makedirs(user_folder, exist_ok=True)

        status_file = self.get_status_file(username, self.vton_img_name, garm_img_name)

        # Write initial status
        with open(status_file, "w") as f:
            json.dump({"status": "processing"}, f)

        def process():
            try:
                time.sleep(5)  # Simulate processing delay

                # Replace this with your actual virtual try-on logic
                success, output_img_one, output_img_two = run_virtual_try_on(username, vton_img_path, garm_img_path)

                if not success:
                    raise Exception("Virtual try-on process failed.")

                status_data = {
                    "status": "completed",
                    "img_one": output_img_one.replace("\\", "/").replace("app/static/",""),
                    "img_two": output_img_two.replace("\\", "/").replace("app/static/","")
                }

                # Write final status
                with open(status_file, "w") as f:
                    json.dump(status_data, f)

            except Exception as e:
                with open(status_file, "w") as f:
                    json.dump({"status": "failed", "error": str(e)}, f)

        # Start the thread for processing
        Thread(target=process).start()

        return jsonify({"success": True, "status": "processing", "message": "Virtual try-on started."})

    def check_status(self, username, vton_img, garm_img):
        username = session.get('user', {}).get('username')
        vton_img_name = self.vton_img_name
        garm_img_name = os.path.splitext(os.path.basename(garm_img))[0].replace(" ", "_")

        status_file = self.get_status_file(username, vton_img_name, garm_img_name)

        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                return jsonify(json.load(f))

        return jsonify({"status": "not_found"})

    def get_status_file(self, username, vton_img, garm_img):
        user_folder = os.path.normpath(os.path.join("app/static/virtual_try_on", username))
        os.makedirs(user_folder, exist_ok=True)
        return os.path.normpath(os.path.join(user_folder, f"{vton_img}_{garm_img}_status.json"))

    def profile(self):
        if 'user' in session:
            # Retrieve the username from session
            username = session['user']['username']
    
            # Query the user_information table for details based on the username
            result = db.session.execute(
                text("SELECT * FROM user_information WHERE username = :username"), 
                {"username": username}
            )
            user_info = result.fetchone()  # Fetch the first matching record
    
            if user_info:
                # Extracting data from the user_info tuple by index
                email = session['user']['email']
                phone = session['user'].get('phone', 'Not Provided')  # Default value if 'phone' is missing
                name = session['user']['name']
                city = session['user'].get('city', 'Not Detected!')
        
                # Assuming the columns are returned in this order:
                profile_pic = user_info[2]  # Update the index as per your table columns
                gender = user_info[3]
                date_of_birth = user_info[4]
                body_type = user_info[5]
                height = user_info[6]
                weight = user_info[7]
                preferred_color = user_info[8]
                preferred_fabrics = user_info[9]
                preferred_styles = user_info[10]
                occasion_types = user_info[11]
                style_goals = user_info[12]
                budget = user_info[13]
                skin_color = user_info[14]
                wardrobe_img = user_info[15]
                user_title = user_info[16]
                user_about_1 = user_info[17]
                user_about_2 = user_info[18]
                session['user']['virtual_try_on_image'] = user_info[19]
                current_date = datetime.now().date()

                if date_of_birth:
                    age = current_date.year - date_of_birth.year - ((current_date.month, current_date.day) < (date_of_birth.month, date_of_birth.day))
                    # Categorize based on age
                    if age < 18:
                        if gender.lower() == "male":
                            gender = "Boys"
                        elif gender.lower() == "female":
                            gender = "Girls"
                        else:
                            gender = "Other"
                    else:
                        if gender.lower() == "male":
                            gender = "Men"
                        elif gender.lower() == "female":
                            gender = "Women"
                else:
                    age = 0
                    gender = "Unisex"
                        
                category_dict = {}
                try:
                    from ai_engine.fashion_recommender import recommend_fashion
                    wardrobe_img_path = None
                    if wardrobe_img:
                        candidate_path = os.path.join(WARDROBE_IMG_FOLDER, wardrobe_img)
                        if os.path.exists(candidate_path):
                            wardrobe_img_path = candidate_path

                    season = session['user'].get('season') or global_season
                    if isinstance(season, str) and season.lower() == 'unknown season':
                        season = None

                    category_dict = recommend_fashion(
                            gender=gender,
                            baseColour=[color.strip() for color in (preferred_color or "").split(',')],
                            preferredFabrics=[fabrics.strip() for fabrics in (preferred_fabrics or "").split(',')],
                            preferredStyles=[styles.strip() for styles in (preferred_styles or "").split(',')],
                            occasionTypes=[occasion.strip() for occasion in (occasion_types or "").split(',')],
                            styleGoals=[goal.strip() for goal in (style_goals or "").split(',')],
                            bodyType=body_type,
                            skin_color=skin_color,
                            season=season,
                            wardrobe_img=wardrobe_img_path
                        )
                except Exception as e:
                    print(f"Fashion recommendation import failed: {e}")
                    category_dict = {}

                recommended_outfits = []
                system_accuracy = 0.0
                top5_precision = 0.0
                try:
                    from ai_engine.hybrid_engine import get_hybrid_recommendation
                    recommended_outfits, hybrid_metrics = get_hybrid_recommendation(username, season)
                    system_accuracy = hybrid_metrics.get('system_accuracy', 0.0)
                    top5_precision = hybrid_metrics.get('top_5_precision', 0.0)
                except Exception as e:
                    print(f"Hybrid recommendation import failed: {e}")

                image_path = "app/static/uploads/profile/" + profile_pic
                # Call the function and get results
                try:
                    from ai_engine.age_gender_skinTone import process_fashion_recommendation
                    skin_tone, gender_sentence, age_sentence, recommend_color, gender_category, detected_age, outfits = process_fashion_recommendation(image_path)
                except Exception as e:
                    print("An error occurred while processing the fashion recommendation:", e)
                    skin_tone = "Unknown"
                    gender_sentence = "Unknown"
                    age_sentence = "Unknown"
                    recommend_color = "Unknown"
                    gender_category = "Unknown"
                    detected_age = "Unknown"
                    outfits = []
                
                # Weather based recommendation
                if season and gender:
                    try:
                        from app.weather_based.recommend_cli import weather_based_recommend
                        weather_recommendations = weather_based_recommend(season, gender)
                    except Exception as e:
                        weather_recommendations = []
                        print(f"Weather recommendation error: {str(e)}")
                else:
                    weather_recommendations = []
                    if not season:
                        print("No season data available (tried form, session, and location)")
                    if not gender:
                        print("No gender data available")
                
                image_wardrobe_path = "app/static/uploads/profile/" + profile_pic
                try:
                    from app.image_based.cli_recommender import rec
                    image_recommend = rec(image_wardrobe_path)
                except Exception as e:
                    print(f"Image recommendation import failed: {e}")
                    image_recommend = []
                
                occasion_types = occasion_types.split(',')
                if occasion_types:
                    all_occasion = {}
                    for occ in occasion_types:
                        if occ == 'Casual Outing':
                            occ = 'Casual'
                        try:
                            from app.occasion.app import recommend
                            reco = recommend(occ, gender, top_items=5)
                        except Exception as e:
                            print(f"Occasion recommendation import failed: {e}")
                            reco = []
                        all_occasion[occ] = reco
                            
                # Format date
                if date_of_birth:
                    date_obj = datetime.strptime(str(date_of_birth), "%Y-%m-%d")
                    f_date_of_birth = date_obj.strftime("%B %d, %Y")
                else:
                    # Handle the case where date_of_birth is None
                    f_date_of_birth = "Unknown"  # Or use a default value like "January 01, 2000"

                if gender.lower() == 'boys':
                    profile_image = 'avatar-1.png'
                elif gender.lower() == 'girls':
                    profile_image = 'avatar-2.png'
                elif gender.lower() == 'men':
                    profile_image = 'male-avatar.png'
                elif gender.lower() == 'women':
                    profile_image = 'avatar-3.png'
                else:
                    profile_image = 'avatar-4.png'

                
                
                # Fetch trove data based on the filters

                # Pass all data to the template
                return render_template(
                    'profile.html', 
                    profile_image=profile_image,
                    username=username, 
                    email=email, 
                    phone=phone, 
                    name=name,
                    city=city,
                    profile_pic=profile_pic,
                    gender=gender,
                    date_of_birth=f_date_of_birth,
                    body_type=body_type,
                    height=height,
                    weight=weight,
                    preferred_color=preferred_color,
                    preferred_fabrics=preferred_fabrics,
                    preferred_styles=preferred_styles,
                    occasion_types=occasion_types,
                    style_goals=style_goals,
                    budget=budget,
                    skin_color=skin_color,
                    wardrobe_img=wardrobe_img,
                    one_word_user=user_title,
                    paragraph_1=user_about_1,
                    paragraph_2=user_about_2,
                    category_dict=category_dict,
                    recommended_outfits=recommended_outfits,
                    system_accuracy=system_accuracy,
                    top5_precision=top5_precision,
                    skin_tone=skin_tone,
                    recommend_color=recommend_color,
                    gender_sentence=gender_sentence,
                    age_sentence=age_sentence,
                    outfits=outfits,
                    season=season,
                    weather_recommendations=weather_recommendations,
                    image_recommend=image_recommend,
                    all_occasion=all_occasion
                )
            else:
                # If no user info is found, redirect to login or show an error
                return redirect(url_for('login'))
        else:
            # If user is not logged in, redirect to login
            return redirect(url_for('login'))

    def quiz(self):
        profile_pic_filename = None
        wardrobe_img_filename = None
        date_of_birth = None
        user_title = None
        user_about_1 = "No title available"  # Default value
        user_about_2 = "No description available"  # Default value
        gender = 'Other' # Default value
        body_type = None # Default value
        skin_color = None

        if request.method == 'POST':
            # Get quiz data from the form
            profile_pic = request.files.get('profile_pic')
            gender = request.form.get('gender') or None
            date_of_birth_str = request.form['date_of_birth'] or None
            body_type = request.form.get('body_type') or None
            height = request.form['height'] or None
            weight = request.form['weight'] or None
            preferred_color = request.form['preferred_color'] or None
            preferred_fabrics = request.form['preferred_fabrics'] or None
            preferred_styles = request.form['preferred_styles'] or None
            occasion_types = request.form['occasion_types'] or None
            style_goals = request.form['style_goals'] or None
            budget = request.form['budget'] or 0
            skin_color = request.form.get('skin_color') or None
            virtual_try_on_image = request.files.get('virtual-try-on')
            wardrobe_img = request.files.get('wardrobe_img')
        


            if date_of_birth_str:
                try:
                    date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()  # Convert to date format
                    current_date = date.today()
                    age = current_date.year - date_of_birth.year - ((current_date.month, current_date.day) < (date_of_birth.month, date_of_birth.day))
                except ValueError:
                    return render_template('quiz.html', title='Fashion Quiz', message="Invalid date format. Please enter a valid date.")

            # Ensure age-based gender adjustment only runs if date_of_birth is valid
            if gender == 'Male' and date_of_birth:
                gender = 'Boys' if age < 18 else 'Men'
            elif gender == 'Female' and date_of_birth:
                gender = 'Girls' if age < 18 else 'Women'


            user_details = session.get('user_details')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            
            if wardrobe_img:
                wardrobe_img_filename = f"{user_details['username']}_{timestamp}_{secure_filename(wardrobe_img.filename)}"
                wardrobe_img_path = os.path.join(WARDROBE_IMG_FOLDER, wardrobe_img_filename)
                wardrobe_img.save(wardrobe_img_path)

            if profile_pic:
                profile_pic_filename = f"{user_details['username']}_{timestamp}_{secure_filename(profile_pic.filename)}"

                profile_pic_path = os.path.join(PROFILE_PIC_FOLDER, profile_pic_filename)

                profile_pic.save(profile_pic_path)
                
            if virtual_try_on_image:
                virtual_try_on_image_filename = f"{user_details['username']}_{secure_filename(virtual_try_on_image.filename)}"
                virtual_try_on_image_path = os.path.join(VIRTUAL_TRY_ON_IMG_FOLDER, virtual_try_on_image_filename)
                virtual_try_on_image.save(virtual_try_on_image_path)

            if user_details['name'] and gender and date_of_birth_str and body_type and height and weight and preferred_color and preferred_fabrics and preferred_styles and occasion_types and style_goals and skin_color:
                prompt = f"""
                    Generate a professionally written, engaging, and personalized "About" section for a user profile in two short paragraphs (90-105 words in total). The content should impress the reader and reflect the user's unique style and preferences. Use the following details:
                    - Name: {user_details['name']}
                    - Gender: {gender}  
                    - Age: {date_of_birth_str}  
                    - Body Type: {body_type}  
                    - Height: {height}  
                    - Weight: {weight}  
                    - Preferred Colors: {preferred_color}  
                    - Preferred Fabrics: {preferred_fabrics}  
                    - Preferred Styles: {preferred_styles}  
                    - Occasion Types: {occasion_types}  
                    - Style Goals: {style_goals}  
                    - Skin Color: {skin_color}

                    Ensure the language is elegant, concise, and makes the user sound fashion-forward and confident. Avoid repetition and use positive, inspiring vocabulary.
                    """
                if chat is not None:
                    try:
                        response = chat.send_message(prompt)
                        paragraph = response.text
                        paragraph = paragraph.split("\n\n")
                        user_about_1 = paragraph[0] if len(paragraph) > 0 else "A stylish individual with an eye for fashion."
                        user_about_2 = paragraph[1] if len(paragraph) > 1 else "Confident, creative, and ready to make smart outfit choices."
                    except Exception as e:
                        user_about_1 = "AI couldn't generate the title"
                        user_about_2 = "AI couldn't generate the description"
                else:
                    user_about_1 = "A stylish individual with a refined sense of personal fashion."
                    user_about_2 = "Confident, modern, and comfortable in curated outfits that reflect their personality."

                prompt = f"""
                    Using the following details about a user, provide one word that best describes the overall style or impression of the individual. Focus solely on the most fitting adjective or noun that reflects the user's fashion preferences, style goals, and persona. Do not add any special characters like asterisks or quotation marks—just return the word itself.

                    Details:
                    - Name: {user_details['name']}
                    - Gender: {gender}
                    - Age: {date_of_birth}
                    - Body Type: {body_type}
                    - Height: {height}
                    - Weight: {weight}
                    - Preferred Colors: {preferred_color}
                    - Preferred Fabrics: {preferred_fabrics}
                    - Preferred Styles: {preferred_styles}
                    - Occasion Types: {occasion_types}
                    - Style Goals: {style_goals}
                    - Skin Color: {skin_color}
                    """
                
                if chat is not None:
                    try:
                        response = chat.send_message(prompt)
                        clean_output = response.text.strip().replace('*', '')  # Removing any asterisks
                        user_title = clean_output
                    except Exception as e:
                        user_title = "Stylish"
                else:
                    user_title = "Stylish"

                # Ensure budget is a valid number (float)
            try:
                budget = float(budget) if budget else None
            except ValueError:
                return render_template('quiz.html', title='Fashion Quiz', message="Please enter a valid number for the budget.")

            # Get user details from session
            user_details = session.get('user_details', {})
            if not user_details:
                return redirect(url_for('login'))  # Redirect if session data is missing


            if user_details:
                # Insert into login table
                insert_query_login = text('INSERT INTO login (name, username, phone, email, password) VALUES (:name, :username, :phone, :email, :password)')
                self.db.session.execute(insert_query_login, {
                    'name': user_details['name'],
                    'username': user_details['username'],
                    'phone': user_details['phone'],
                    'email': user_details['email'],
                    'password': user_details['password']
                })
                self.db.session.commit()

                # Insert into user_information table
                insert_query_info = text('''INSERT INTO user_information (username, profile_pic, gender, date_of_birth, body_type, height, weight, preferred_color, preferred_fabrics, preferred_styles, occasion_types, style_goals, budget, skin_color, wardrobe_img, user_title, user_about_1, user_about_2, virtual_try_on_image)
                                        VALUES (:username, :profile_pic, :gender, :date_of_birth, :body_type, :height, :weight, :preferred_color, :preferred_fabrics, :preferred_styles, :occasion_types, :style_goals, :budget, :skin_color, :wardrobe_img, :user_title, :user_about_1, :user_about_2, :virtual_try_on_image)''')
                self.db.session.execute(insert_query_info, {
                    'username': user_details['username'],
                    'profile_pic': profile_pic_filename or None,
                    'gender': gender or None,
                    'date_of_birth': date_of_birth or None,
                    'body_type': body_type or None,
                    'height': height or None,
                    'weight': weight or None,
                    'preferred_color': preferred_color or None,
                    'preferred_fabrics': preferred_fabrics or None,
                    'preferred_styles': preferred_styles or None,
                    'occasion_types': occasion_types or None,
                    'style_goals': style_goals or None,
                    'budget': budget or None,  # Ensure this is a valid number
                    'skin_color': skin_color,
                    'wardrobe_img': wardrobe_img_filename or None,
                    'user_title': user_title or None,
                    'user_about_1': user_about_1 or None,
                    'user_about_2': user_about_2 or None,
                    'virtual_try_on_image': virtual_try_on_image_filename if virtual_try_on_image_filename else None
                })
                self.db.session.commit()

                # Clear session data after the quiz
                session.pop('user_details', None)

                # Redirect to profile page after successful quiz
                return redirect(url_for('profile'))

            else:
                # If user details are missing from session, redirect to signup
                return redirect(url_for('login'))

        # If the request is GET, render the quiz page
        return render_template('quiz.html', title='Fashion Quiz')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set limit to 16MB

# Initialize the classes
Dashboard(app)
Login(app, db)
Profile(app, db)

if __name__ == '__main__':
    app.secret_key = 'manojrajgopal'  # Ensure you have a secret key for sessions
    app.run(debug=True)