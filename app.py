from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify,send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from models import (
    init_db, get_farmer_by_email, insert_farmer,
    get_vendor_by_email, insert_vendor,
    get_charity_by_email, insert_charity,
    insert_produce, get_all_produce,
    insert_purchase, get_vendor_purchases,
    get_produce_by_id, get_farmer_purchases,
    get_farmer_revenue, get_farmer_produce,
    insert_donation, get_vendor_donations,
    get_available_donations, get_charity_by_id, update_donation_status
)
import base64
import os
import google.generativeai as genai
import requests
import uuid
from gtts import gTTS
import logging
from dotenv import load_dotenv
import speech_recognition as sr
from bs4 import BeautifulSoup
import sqlite3
from ai_chat import create_chat_routes
from news_scraper import scrape_agri_news

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = os.getenv("FLASK_SECRET_KEY") 

genai.configure(api_key=os.getenv("GENAI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")

API_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a directory for audio files
AUDIO_DIR = os.path.join(os.getcwd(), "audio")
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logging.error("GEMINI_API_KEY not found in .env file")
    raise ValueError("GEMINI_API_KEY is required in .env file")
logging.info("GEMINI_API_KEY loaded successfully")
genai.configure(api_key=api_key)

# Initialize Gemini 1.5 Flash model
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    logging.info("Gemini model initialized")
except Exception as e:
    logging.error(f"Failed to initialize Gemini model: {str(e)}")
    raise

# Initialize speech recognizer (optional)
speech_recognition_enabled = False
try:
    import pyaudio
    recognizer = sr.Recognizer()
    speech_recognition_enabled = True
    logging.info("Speech recognizer initialized with PyAudio")
except ImportError as e:
    logging.warning("PyAudio not installed: Speech recognition will be disabled")
except Exception as e:
    logging.error(f"Failed to initialize speech recognizer: {str(e)}")
    logging.warning("Speech recognition will be disabled")

init_db()

create_chat_routes(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    user_input = request.form.get("text_input", "").strip()
    language = request.form.get("language", "en")  # Default to English
    logging.info(f"Received text input: {user_input}, language: {language}")
    if not user_input:
        logging.warning("Empty text input received")
        return jsonify({"response": "Error: No input provided", "audio_url": None}), 400
    
    # Map language codes
    language_map = {
        "en": {"name": "English", "gtts_code": "en", "speech_code": "en-IN"},
        "hi": {"name": "Hindi", "gtts_code": "hi", "speech_code": "hi-IN"},
        "te": {"name": "Telugu", "gtts_code": "te", "speech_code": "te-IN"}
    }
    lang_info = language_map.get(language, language_map["en"])
    
    # Construct prompt with language instruction
    prompt = f"Respond to the following in {lang_info['name']}: {user_input}"
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        logging.info(f"Gemini response: {response_text[:50]}...")
        
        # Generate audio with gTTS
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        try:
            tts = gTTS(text=response_text, lang=lang_info["gtts_code"], slow=False)
            tts.save(audio_path)
            logging.debug(f"Audio file saved: {audio_path}")
        except Exception as e:
            logging.error(f"gTTS error: {str(e)}")
            return jsonify({"response": response_text, "audio_url": None}), 200
        
        audio_url = f"/audio/{audio_filename}"
        return jsonify({"response": response_text, "audio_url": audio_url}), 200
    except Exception as e:
        logging.error(f"Text processing error: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}", "audio_url": None}), 500

@app.route("/process_voice", methods=["POST"])
def process_voice():
    if not speech_recognition_enabled:
        return jsonify({"success": False, "message": "Speech recognition is not enabled on this server"}), 400
    language = request.form.get("language", "en")  # Default to English
    logging.info(f"Starting voice input processing, language: {language}")
    
    # Map language codes
    language_map = {
        "en": {"name": "English", "gtts_code": "en", "speech_code": "en-IN"},
        "hi": {"name": "Hindi", "gtts_code": "hi", "speech_code": "hi-IN"},
        "te": {"name": "Telugu", "gtts_code": "te", "speech_code": "te-IN"}
    }
    lang_info = language_map.get(language, language_map["en"])
    
    try:
        with sr.Microphone() as source:
            logging.debug("Adjusting for ambient noise")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logging.debug("Listening for audio")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            logging.debug("Recognizing audio")
            user_input = recognizer.recognize_google(audio, language=lang_info["speech_code"])
            logging.info(f"Recognized voice input: {user_input}")
            
            # Construct prompt with language instruction
            prompt = f"Respond to the following in {lang_info['name']}: {user_input}"
            
            response = model.generate_content(prompt)
            response_text = response.text
            logging.info(f"Gemini response: {response_text[:50]}...")
            
            # Generate audio with gTTS
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            try:
                tts = gTTS(text=response_text, lang=lang_info["gtts_code"], slow=False)
                tts.save(audio_path)
                logging.debug(f"Audio file saved: {audio_path}")
            except Exception as e:
                logging.error(f"gTTS error: {str(e)}")
                return jsonify({"input": user_input, "response": response_text, "audio_url": None}), 200
            
            audio_url = f"/audio/{audio_filename}"
            return jsonify({"input": user_input, "response": response_text, "audio_url": audio_url}), 200
    except sr.UnknownValueError:
        logging.error("Speech recognition failed: Could not understand audio")
        return jsonify({"response": "Sorry, I couldn't understand the audio.", "audio_url": None}), 400
    except sr.RequestError as e:
        logging.error(f"Speech recognition error: {str(e)}")
        return jsonify({"response": f"Speech recognition error: {str(e)}", "audio_url": None}), 500
    except Exception as e:
        logging.error(f"Voice processing error: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}", "audio_url": None}), 500

@app.route("/audio/<filename>")
def serve_audio(filename):
    try:
        return send_from_directory(AUDIO_DIR, filename)
    except Exception as e:
        logging.error(f"Error serving audio file {filename}: {str(e)}")
        return "Audio file not found", 404

@app.route("/Farmerlogin", methods=["GET", "POST"])
def Farmerlogin():
    if request.method == "POST":
        if request.form.get("action") == "login":  # Login action
            email = request.form["logemail"]
            password = request.form["logpass"]
            
            farmer = get_farmer_by_email(email)
            
            if farmer and check_password_hash(farmer[3], password):  # Check password hash
                session["farmer_id"] = farmer[0]  # Store farmer id in session
                flash("Login successful!", "success")
                return redirect(url_for("farmerdash"))
            else:
                flash("Invalid credentials. Please try again.", "danger")
                
        elif request.form.get("action") == "signup":  # Signup action
            name = request.form["logname"]
            email = request.form["logemail"]
            password = request.form["logpass"]
            
            hashed_password = generate_password_hash(password)
            
            insert_farmer(name, email, hashed_password)
            flash("Sign-up successful! Please log in.", "success")
            return redirect(url_for("Farmerlogin"))
    
    return render_template("Farmerlogin.html")

@app.route('/farmerdash')
def farmerdash():
    if "farmer_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("Farmerlogin"))
    
    # Get purchase history, revenue data, and posted produce for this farmer
    purchase_history = get_farmer_purchases(session["farmer_id"])
    revenue_data = get_farmer_revenue(session["farmer_id"])
    posted_produce = get_farmer_produce(session["farmer_id"])
    
    return render_template("farmerdash.html", 
                         purchase_history=purchase_history,
                         revenue_data=revenue_data,
                         posted_produce=posted_produce)

@app.route("/Vendorlogin", methods=["GET", "POST"])
def Vendorlogin():
    if request.method == "POST":
        if request.form.get("action") == "login":
            email = request.form["logemail"]
            password = request.form["logpass"]
            vendor = get_vendor_by_email(email)

            if vendor and check_password_hash(vendor[3], password):
                session["vendor_id"] = vendor[0]
                flash("Login successful!", "success")
                return redirect(url_for("vendordash"))
            else:
                flash("Invalid credentials.", "danger")

        elif request.form.get("action") == "signup":
            name = request.form["logname"]
            email = request.form["logemail"]
            password = request.form["logpass"]
            hashed_password = generate_password_hash(password)
            insert_vendor(name, email, hashed_password)
            flash("Sign-up successful! Please log in.", "success")
            return redirect(url_for("Vendorlogin"))

    return render_template("Vendorlogin.html")


@app.route("/Charitylogin", methods=["GET", "POST"])
def Charitylogin():
    if request.method == "POST":
        if request.form.get("action") == "login":
            email = request.form["logemail"]
            password = request.form["logpass"]
            charity = get_charity_by_email(email)

            if charity and check_password_hash(charity[3], password):
                session["charity_id"] = charity[0]
                flash("Login successful!", "success")
                return redirect(url_for("charity_dashboard"))
            else:
                flash("Invalid credentials.", "danger")

        elif request.form.get("action") == "signup":
            name = request.form["logname"]
            email = request.form["logemail"]
            password = request.form["logpass"]
            hashed_password = generate_password_hash(password)
            insert_charity(name, email, hashed_password)
            flash("Sign-up successful! Please log in.", "success")
            return redirect(url_for("Charitylogin"))

    return render_template("Charitylogin.html")

@app.route('/charitydash')
def charity_dashboard():
    if 'charity_id' not in session:
        flash('Please login as a charity first', 'error')
        return redirect(url_for('Charitylogin'))
    
    # Get available donations
    donations = get_available_donations()
    charity = get_charity_by_id(session['charity_id'])
    return render_template('charitydash.html', donations=donations, charity_name=charity[1])

@app.route('/claim_donation/<int:donation_id>', methods=['POST'])
def claim_donation(donation_id):
    if 'charity_id' not in session:
        flash('Please login as a charity first', 'error')
        return redirect(url_for('Charitylogin'))
    
    if update_donation_status(donation_id, 'claimed'):
        flash('Donation claimed successfully!', 'success')
    else:
        flash('Error claiming donation. Please try again.', 'error')
    
    return redirect(url_for('charity_dashboard'))

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json["message"]
    print(f"Received message: {user_input}")  # Debug logging

    prompt = [
        "now i will ask in telugu and you should reply in telugu only okay and in 1 sentence and fast",
        "అలాగే. మీరు తెలుగులో అడిగితే, నేను తప్పకుండా తెలుగులోనే బదులిస్తాను. అడగండి.",
        user_input
    ]

    response = model.generate_content(prompt)
    reply = response.text
    print(f"Generated reply: {reply}")  # Debug logging

    audio_url = gtts_text_to_speech(reply)
    print(f"Generated audio URL: {audio_url}")  # Debug logging

    return jsonify({"reply": reply, "audio_url": audio_url})

def gtts_text_to_speech(text):
    try:
        # Create a unique filename
        filename = f"audio_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join("static", filename)
        
        # Make sure the static directory exists
        os.makedirs("static", exist_ok=True)
        
        # Create gTTS object
        tts = gTTS(text=text, lang='te', slow=False)
        
        # Save to file
        tts.save(filepath)
        print(f"Audio content written to file {filepath}")
        
        # Return the URL to access the file
        audio_url = url_for('static', filename=filename)
        return audio_url
    
    except Exception as e:
        print(f"Error in gTTS: {str(e)}")
        return None

@app.route("/rrb")
def rrb_redirect():
    return redirect(url_for('rrb_info'))

@app.route("/rrb-info")
def rrb_info():
    # You could load RRB data from a database in a real implementation
    rrbs = [
        {"name": "Andhra Pradesh Grameena Vikas Bank", "headquarter": "Warangal", "districts": "Warangal, Khammam, Nalgonda, etc.", "lat": 17.9689, "lng": 79.5941},
        {"name": "Telangana Grameena Bank", "headquarter": "Hyderabad", "districts": "Hyderabad, Rangareddy, Medak, etc.", "lat": 17.3850, "lng": 78.4867},
        {"name": "Chaitanya Godavari Grameena Bank", "headquarter": "Guntur", "districts": "Guntur, Krishna, West Godavari, etc.", "lat": 16.3067, "lng": 80.4365},
        {"name": "Aryavart Bank", "headquarter": "Lucknow", "districts": "Lucknow, Kanpur, Agra, etc.", "lat": 26.8467, "lng": 80.9462},
        {"name": "Baroda Uttar Pradesh Gramin Bank", "headquarter": "Baroda", "districts": "Agra, Aligarh, Allahabad, etc.", "lat": 27.1751, "lng": 78.0353},
        {"name": "Bihar Gramin Bank", "headquarter": "Patna", "districts": "Patna, Gaya, Nalanda, etc.", "lat": 25.5941, "lng": 85.1376},
        {"name": "Chhattisgarh Rajya Gramin Bank", "headquarter": "Raipur", "districts": "Raipur, Durg, Bilaspur, etc.", "lat": 21.2514, "lng": 81.6296},
        {"name": "Dena Gujarat Gramin Bank", "headquarter": "Gandhinagar", "districts": "Vadodara, Surat, Gandhinagar, etc.", "lat": 23.0225, "lng": 72.5714},
        {"name": "Goa Gramin Bank", "headquarter": "Panaji", "districts": "North Goa, South Goa", "lat": 15.2993, "lng": 74.1240},
        {"name": "Haryana Gramin Bank", "headquarter": "Rohtak", "districts": "Rohtak, Hisar, Karnal, etc.", "lat": 28.8930, "lng": 76.7673},
        {"name": "Himachal Gramin Bank", "headquarter": "Mandi", "districts": "Mandi, Kullu, Kangra, etc.", "lat": 32.0841, "lng": 77.1005},
        {"name": "Jharkhand Gramin Bank", "headquarter": "Ranchi", "districts": "Ranchi, Dhanbad, Jamshedpur, etc.", "lat": 23.3441, "lng": 85.3096},
        {"name": "Karnataka Vikas Grameena Bank", "headquarter": "Bagalkot", "districts": "Bagalkot, Dharwad, Belagavi, etc.", "lat": 15.1261, "lng": 75.6015},
        {"name": "Kerala Gramin Bank", "headquarter": "Malappuram", "districts": "Malappuram, Kozhikode, Thrissur, etc.", "lat": 11.1022, "lng": 76.0719},
        {"name": "Madhya Pradesh Gramin Bank", "headquarter": "Indore", "districts": "Indore, Bhopal, Ujjain, etc.", "lat": 22.7196, "lng": 75.8577},
        {"name": "Maharashtra Gramin Bank", "headquarter": "Nashik", "districts": "Nashik, Thane, Pune, etc.", "lat": 19.9975, "lng": 73.7885},
        {"name": "Manipur Rural Bank", "headquarter": "Imphal", "districts": "Imphal, Thoubal, Bishnupur, etc.", "lat": 24.8138, "lng": 93.9584},
        {"name": "Meghalaya Rural Bank", "headquarter": "Shillong", "districts": "East Khasi Hills, West Khasi Hills, etc.", "lat": 25.5788, "lng": 91.8933},
        {"name": "Mizoram Rural Bank", "headquarter": "Aizawl", "districts": "Aizawl, Lunglei, Champhai, etc.", "lat": 23.7270, "lng": 92.7176},
        {"name": "Nagaland Rural Bank", "headquarter": "Dimapur", "districts": "Dimapur, Kohima, Mokokchung, etc.", "lat": 25.9078, "lng": 93.7198},
        {"name": "Odisha Gramya Bank", "headquarter": "Bhubaneswar", "districts": "Cuttack, Berhampur, Balasore, etc.", "lat": 20.2961, "lng": 85.8189},
        {"name": "Punjab Gramin Bank", "headquarter": "Jalandhar", "districts": "Jalandhar, Ludhiana, Amritsar, etc.", "lat": 31.3260, "lng": 75.5762},
        {"name": "Rajasthan Gramin Bank", "headquarter": "Ajmer", "districts": "Ajmer, Udaipur, Chittorgarh, etc.", "lat": 26.4511, "lng": 74.6399},
        {"name": "Saurashtra Gramin Bank", "headquarter": "Rajkot", "districts": "Rajkot, Junagadh, Jamnagar, etc.", "lat": 22.3039, "lng": 70.8022},
        {"name": "Sikkim Gramin Bank", "headquarter": "Gangtok", "districts": "East Sikkim, West Sikkim, etc.", "lat": 27.3300, "lng": 88.6126},
        {"name": "Tamil Nadu Grama Bank", "headquarter": "Chennai", "districts": "Chennai, Coimbatore, Madurai, etc.", "lat": 13.0827, "lng": 80.2707},
        {"name": "Uttarakhand Gramin Bank", "headquarter": "Dehradun", "districts": "Dehradun, Haridwar, Nainital, etc.", "lat": 30.3165, "lng": 78.0322},
        {"name": "Uttar Pradesh Gramin Bank", "headquarter": "Kanpur", "districts": "Kanpur, Allahabad, Varanasi, etc.", "lat": 26.4499, "lng": 80.3319},
        {"name": "West Bengal Gramin Bank", "headquarter": "Kolkata", "districts": "Kolkata, Howrah, South 24 Parganas, etc.", "lat": 22.5726, "lng": 88.3639},
        {"name": "Bihar Gramin Bank", "headquarter": "Patna", "districts": "Patna, Gaya, Nalanda, etc.", "lat": 25.5941, "lng": 85.1376},
        {"name": "Madhya Pradesh Rajya Gramin Bank", "headquarter": "Indore", "districts": "Indore, Bhopal, Ujjain, etc.", "lat": 22.7196, "lng": 75.8577},
        {"name": "Tripura Gramin Bank", "headquarter": "Agartala", "districts": "West Tripura, South Tripura, etc.", "lat": 23.8315, "lng": 91.2867},
        {"name": "Nagaland Rural Bank", "headquarter": "Dimapur", "districts": "Dimapur, Kohima, Mokokchung, etc.", "lat": 25.9078, "lng": 93.7198}
    ]
    return render_template("rrb_info.html", rrbs=rrbs)

@app.route("/vegprices")
def veg_prices():
    prices = get_veg_price_news()
    return render_template('vegprices.html', prices=prices)

@app.route('/submit-produce', methods=['POST'])
def submit_produce():
    data = request.json
    farmer_id = data['farmer_id']  # Farmer's ID should be passed along
    produce = data['produce']
    quantity = data['quantity']
    price = data['price']
    
    insert_produce(farmer_id, produce, quantity, price)
    
    return jsonify({"status": "success"})

@app.route('/vendordash')
def vendordash():
    if "vendor_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("Vendorlogin"))
    
    # Get all available produce
    produce_list = get_all_produce()
    
    # Get vendor's purchase history
    purchase_history = get_vendor_purchases(session["vendor_id"])
    
    return render_template(
        "vendordash.html", 
        produce=produce_list,
        purchase_history=purchase_history
    )

@app.route("/buy_produce", methods=["POST"])
def buy_produce():
    if "vendor_id" not in session:
        return jsonify({"success": False, "message": "Please log in first!"}), 401
    
    try:
        data = request.json
        produce_id = data.get("produce_id")
        quantity = float(data.get("quantity", 0))
        
        if not produce_id or quantity <= 0:
            return jsonify({"success": False, "message": "Invalid input"}), 400
        
        # Get produce details
        produce = get_produce_by_id(produce_id)
        if not produce:
            return jsonify({"success": False, "message": "Produce not found"}), 404
        
        # Attempt to make the purchase
        success, message = insert_purchase(
            produce_id=produce_id,
            vendor_id=session["vendor_id"],
            quantity=quantity,
            price_per_unit=produce[3]  # price is at index 3 in produce table
        )
        
        if success:
            # Get updated purchase history
            purchase_history = get_vendor_purchases(session["vendor_id"])
            latest_purchase = purchase_history[0] if purchase_history else None
            
            return jsonify({
                "success": True,
                "message": "Purchase successful",
                "purchase": {
                    "id": latest_purchase[0],
                    "produce_name": latest_purchase[1],
                    "quantity": latest_purchase[2],
                    "price_per_unit": latest_purchase[3],
                    "total_price": latest_purchase[4],
                    "date": latest_purchase[5],
                    "farmer_name": latest_purchase[6]
                } if latest_purchase else None
            })
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/vendor/donate', methods=['GET', 'POST'])
def vendor_donate():
    if 'vendor_id' not in session:
        flash('Please login as a vendor first', 'error')
        return redirect(url_for('Vendorlogin'))

    if request.method == 'POST':
        item_name = request.form.get('item_name')
        quantity = float(request.form.get('quantity'))
        vendor_address = request.form.get('vendor_address')
        vendor_phone = request.form.get('vendor_phone')
        vendor_id = session['vendor_id']

        if insert_donation(vendor_id, item_name, quantity, vendor_address, vendor_phone):
            flash('Donation added successfully!', 'success')
        else:
            flash('Error adding donation. Please try again.', 'error')
        
        return redirect(url_for('vendor_donate'))

    # Get vendor's previous donations
    donations = get_vendor_donations(session['vendor_id'])
    return render_template('vendor_donate.html', donations=donations)

@app.route('/weather')
def weather():
    if "farmer_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("Farmerlogin"))
    return render_template("weather.html")

@app.route('/soil')
def soil():
    if "farmer_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("Farmerlogin"))
    return render_template("soil.html")

@app.route('/post_produce', methods=['GET', 'POST'])
def post_produce():
    if "farmer_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("Farmerlogin"))
    
    if request.method == 'POST':
        try:
            produce_name = request.form.get('produce_name')
            quantity = float(request.form.get('quantity'))
            price = float(request.form.get('price'))
            
            if not produce_name or not quantity or not price:
                flash("Please fill in all fields!", "danger")
                return redirect(url_for("post_produce"))
            
            if quantity <= 0 or price <= 0:
                flash("Quantity and price must be greater than 0!", "danger")
                return redirect(url_for("post_produce"))
            
            # Insert the produce into the database
            insert_produce(session["farmer_id"], produce_name, quantity, price)
            flash("Produce posted successfully!", "success")
            return redirect(url_for("farmerdash"))
            
        except ValueError:
            flash("Please enter valid numbers for quantity and price!", "danger")
            return redirect(url_for("post_produce"))
        except Exception as e:
            flash("Error posting produce. Please try again!", "danger")
            return redirect(url_for("post_produce"))
        
    return render_template("post_produce.html")

@app.route("/news")
def news():
    # Get the latest news
    news_items = scrape_agri_news()
    return render_template("news.html", news_items=news_items)

def get_veg_price_news():
    try:
        # The correct URL
        URL = "https://vegetablemarketprice.com/market/andhrapradesh/today"
        
        # Add headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch page, status code: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # The data appears to be in a table structure
        prices = []
        
        # Find all table rows (excluding header)
        rows = soup.find_all("tr")[1:]  # Skip the header row
        
        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 5:  # Make sure we have enough columns
                vegetable_name = columns[0].get_text(strip=True)
                wholesale_price = columns[1].get_text(strip=True)
                retail_price = columns[2].get_text(strip=True)
                shopping_mall_price = columns[3].get_text(strip=True)
                unit = columns[4].get_text(strip=True)
                
                prices.append({
                    "vegetable": vegetable_name,
                    "wholesale_price": wholesale_price,
                    "retail_price": retail_price,
                    "shopping_mall_price": shopping_mall_price,
                    "unit": unit
                })
        
        return prices
    except Exception as e:
        print(f"Error scraping vegetable prices: {e}")
        return []

if __name__ == '__main__':
    app.run(debug=True)
