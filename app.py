from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app)

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            temperature REAL,
            humidity REAL,
            rainfall REAL,
            wind_speed REAL,
            weather_condition TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT UNIQUE NOT NULL,
            temp_min REAL,
            temp_max REAL,
            rainfall_min REAL,
            rainfall_max REAL,
            soil_type TEXT,
            climate_type TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soils (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soil_name TEXT UNIQUE NOT NULL,
            description TEXT,
            ph_min REAL,
            ph_max REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT,
            climate_type TEXT,
            soil_type TEXT,
            suitability INTEGER,
            recommendation_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diseases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT,
            disease_name TEXT,
            description TEXT,
            symptoms TEXT,
            causes TEXT,
            pesticide TEXT,
            fertilizer TEXT,
            prevention TEXT,
            water_requirement TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT,
            price REAL,
            unit TEXT,
            trend TEXT,
            market_name TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Black Soil', 'Rich in iron, lime, and calcium. Good for cotton.', 6.5, 8.0))
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Red Soil', 'Rich in iron oxide. Good for groundnut and millets.', 5.5, 7.0))
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Sandy Soil', 'Well-draining, low nutrient retention.', 6.0, 7.5))
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Clay Soil', 'High water retention, fertile.', 6.0, 7.5))
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Loamy Soil', 'Ideal soil type. Good water retention and fertility.', 6.0, 7.0))
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Laterite Soil', 'Rich in iron and aluminum. Good for cashew.', 5.0, 6.5))
    cursor.execute('INSERT OR IGNORE INTO soils (soil_name, description, ph_min, ph_max) VALUES (?,?,?,?)',
                   ('Alluvial Soil', 'Fertile, good for rice and wheat.', 6.5, 8.0))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crop', methods=['GET', 'POST'])
def crop():
    if request.method == 'POST':
        # Save location data to session
        session['location'] = {
            'state': request.form.get('state'),
            'district': request.form.get('district'),
            'village': request.form.get('village'),
            'location': request.form.get('location'),
            'climate': request.form.get('climate'),
            'temperature': request.form.get('temperature'),
            'humidity': request.form.get('humidity'),
            'rainfall': request.form.get('rainfall'),
            'wind_speed': request.form.get('wind_speed'),
            'weather_condition': request.form.get('weather_condition')
        }
        return redirect(url_for('recommendation'))
    return render_template('crop.html')

@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    if request.method == 'POST':
        # Save crop data to session
        session['crop_data'] = {
            'crop_name': request.form.get('crop_name'),
            'soil_type': request.form.get('soil_type')
        }
        return redirect(url_for('disease'))
    
    # Get data from session
    location_data = session.get('location', {})
    crop_data = session.get('crop_data', {})
    
    # Simple recommendation logic
    crop_name = crop_data.get('crop_name', '')
    climate = location_data.get('climate', '')
    soil_type = crop_data.get('soil_type', '')
    temperature = location_data.get('temperature', '')
    
    # Crop database
    crop_db = {
        'Rice': {'temp': (20, 35), 'climate': ['Summer', 'Rainy'], 'soil': ['Clay Soil', 'Loamy Soil', 'Alluvial Soil']},
        'Wheat': {'temp': (15, 25), 'climate': ['Winter', 'Spring'], 'soil': ['Loamy Soil', 'Alluvial Soil', 'Black Soil']},
        'Maize': {'temp': (20, 32), 'climate': ['Summer', 'Rainy'], 'soil': ['Sandy Soil', 'Loamy Soil', 'Alluvial Soil']},
        'Cotton': {'temp': (25, 35), 'climate': ['Summer'], 'soil': ['Black Soil', 'Red Soil', 'Alluvial Soil']},
        'Sugarcane': {'temp': (20, 35), 'climate': ['Summer', 'Rainy'], 'soil': ['Clay Soil', 'Loamy Soil', 'Alluvial Soil']},
        'Groundnut': {'temp': (25, 35), 'climate': ['Summer', 'Rainy'], 'soil': ['Sandy Soil', 'Red Soil', 'Laterite Soil']},
        'Tomato': {'temp': (18, 30), 'climate': ['Spring', 'Summer'], 'soil': ['Loamy Soil', 'Sandy Soil', 'Red Soil']},
        'Onion': {'temp': (15, 28), 'climate': ['Spring', 'Winter'], 'soil': ['Loamy Soil', 'Alluvial Soil', 'Sandy Soil']},
        'Banana': {'temp': (25, 35), 'climate': ['Summer', 'Rainy'], 'soil': ['Loamy Soil', 'Clay Soil', 'Alluvial Soil']},
        'Millets': {'temp': (25, 40), 'climate': ['Summer', 'Rainy'], 'soil': ['Sandy Soil', 'Red Soil', 'Laterite Soil']}
    }
    
    recommendation = {
        'suitable': False,
        'message': '',
        'details': {},
        'alternatives': []
    }
    
    if crop_name in crop_db:
        crop_info = crop_db[crop_name]
        suitable = True
        reasons = []
        
        # Check climate
        if climate not in crop_info['climate']:
            suitable = False
            reasons.append(f"Climate '{climate}' is not optimal for {crop_name}")
        
        # Check soil
        if soil_type and soil_type not in crop_info['soil']:
            suitable = False
            reasons.append(f"'{soil_type}' is not ideal for {crop_name}")
        
        # Check temperature
        if temperature:
            try:
                temp = float(temperature)
                if not (crop_info['temp'][0] <= temp <= crop_info['temp'][1]):
                    suitable = False
                    reasons.append(f"Temperature {temp}°C is outside optimal range")
            except:
                pass
        
        if suitable:
            recommendation['suitable'] = True
            recommendation['message'] = f'✅ {crop_name} is suitable for the selected weather and soil conditions!'
            recommendation['details'] = {
                'crop': crop_name,
                'optimal_temperature': f"{crop_info['temp'][0]} - {crop_info['temp'][1]}°C",
                'suitable_soils': ', '.join(crop_info['soil']),
                'suitable_climate': ', '.join(crop_info['climate'])
            }
        else:
            recommendation['suitable'] = False
            recommendation['message'] = f'⚠️ {crop_name} may not be suitable for the selected conditions.'
            recommendation['reasons'] = reasons
            
            # Find alternatives
            alternatives = []
            for alt_crop, alt_info in crop_db.items():
                if alt_crop != crop_name:
                    score = 0
                    alt_reasons = []
                    if climate in alt_info['climate']:
                        score += 1
                        alt_reasons.append(f"Grows well in {climate} climate")
                    if soil_type in alt_info['soil']:
                        score += 1
                        alt_reasons.append(f"Compatible with {soil_type}")
                    if score >= 1:
                        alternatives.append({
                            'crop': alt_crop,
                            'reasons': alt_reasons,
                            'details': f"Temp: {alt_info['temp'][0]}-{alt_info['temp'][1]}°C, Soil: {', '.join(alt_info['soil'][:2])}"
                        })
            recommendation['alternatives'] = sorted(alternatives, key=lambda x: len(x['reasons']), reverse=True)[:5]
    
    return render_template('recommendation.html', recommendation=recommendation)

@app.route('/disease', methods=['GET', 'POST'])
def disease():
    if request.method == 'POST':
        session['disease_data'] = {
            'crop_name': request.form.get('crop_name'),
            'disease_name': request.form.get('disease_name')
        }
        return redirect(url_for('market'))
    
    disease_data = session.get('disease_data', {})
    crop_name = disease_data.get('crop_name', '')
    disease_name = disease_data.get('disease_name', '')
    
    # Disease database
    disease_db = {
        'Rice': {
            'Blast': {
                'description': 'Rice blast is a fungal disease caused by Magnaporthe oryzae.',
                'symptoms': 'Elliptical spots on leaves with gray centers and brown borders.',
                'causes': 'High humidity, moderate temperatures (24-28°C), excess nitrogen.',
                'pesticide': 'Tricyclazole or Isoprothiolane at 0.6-0.8 kg/ha',
                'fertilizer': 'Balanced NPK with reduced nitrogen. Apply silicon fertilizers.',
                'prevention': 'Use resistant varieties, balanced fertilization, proper spacing.',
                'water_requirement': 'Maintain standing water, avoid drought stress'
            },
            'Brown Spot': {
                'description': 'Brown spot is a fungal disease caused by Bipolaris oryzae.',
                'symptoms': 'Small brown oval spots on leaves, resembling sesame seeds.',
                'causes': 'Poor soil fertility, nutrient deficiency, high humidity.',
                'pesticide': 'Propiconazole 0.1% or Mancozeb 0.25%',
                'fertilizer': 'Apply balanced NPK, especially potassium.',
                'prevention': 'Maintain soil fertility, balanced fertilization.',
                'water_requirement': 'Proper water management'
            },
            'Leaf Blight': {
                'description': 'Bacterial leaf blight caused by Xanthomonas oryzae pv. oryzae.',
                'symptoms': 'Yellowish-green lesions along leaf margins, turning white-yellow.',
                'causes': 'Wounds from wind, rain, or insects. High humidity.',
                'pesticide': 'Streptomycin sulfate 100 ppm + Copper oxychloride 0.2%',
                'fertilizer': 'Reduced nitrogen, adequate potassium.',
                'prevention': 'Avoid over-fertilization, use resistant varieties.',
                'water_requirement': 'Maintain shallow water depth'
            }
        },
        'Tomato': {
            'Early Blight': {
                'description': 'Early blight is a fungal disease caused by Alternaria solani.',
                'symptoms': 'Dark brown spots with concentric rings on leaves and stems.',
                'causes': 'Warm temperatures (24-29°C), high humidity, poor air circulation.',
                'pesticide': 'Chlorothalonil 0.2% or Mancozeb 0.25%',
                'fertilizer': 'Balanced NPK with adequate potassium.',
                'prevention': 'Crop rotation, proper spacing, remove infected leaves.',
                'water_requirement': 'Regular watering, avoid overhead irrigation'
            },
            'Late Blight': {
                'description': 'Late blight is a fungal disease caused by Phytophthora infestans.',
                'symptoms': 'Water-soaked spots on leaves, white fungal growth on undersides.',
                'causes': 'Cool, wet conditions (15-20°C), high humidity.',
                'pesticide': 'Metalaxyl + Mancozeb or Fosetyl-Al',
                'fertilizer': 'Balanced nutrition with emphasis on potassium.',
                'prevention': 'Use resistant varieties, proper spacing, remove infected plants.',
                'water_requirement': 'Avoid over-irrigation, provide good drainage'
            },
            'Leaf Curl': {
                'description': 'Tomato leaf curl is caused by tomato yellow leaf curl virus.',
                'symptoms': 'Yellowing and curling of leaf margins, stunted growth.',
                'causes': 'Whitefly vector, warm temperatures, virus transmission.',
                'pesticide': 'Apply neem oil or insecticidal soap for whitefly control.',
                'fertilizer': 'Balanced NPK with micronutrients.',
                'prevention': 'Use virus-resistant varieties, install insect netting.',
                'water_requirement': 'Regular watering, avoid water stress'
            }
        },
        'Cotton': {
            'Wilt': {
                'description': 'Cotton wilt is caused by Fusarium oxysporum f.sp. vasinfectum.',
                'symptoms': 'Yellowing of leaves starting from bottom, wilting, vascular discoloration.',
                'causes': 'Soil-borne fungus, warm temperatures (25-35°C).',
                'pesticide': 'Carbendazim 0.1% or Tridemorph 0.1% as drench',
                'fertilizer': 'Balanced NPK with emphasis on potassium.',
                'prevention': 'Use resistant varieties, crop rotation, maintain soil pH.',
                'water_requirement': 'Proper irrigation, avoid waterlogging'
            },
            'Root Rot': {
                'description': 'Root rot is caused by Rhizoctonia solani.',
                'symptoms': 'Wilting, brown to black lesions on roots, stunted growth.',
                'causes': 'Wet soil conditions, poor drainage, high soil temperature.',
                'pesticide': 'Apply Trichoderma viride as biological control.',
                'fertilizer': 'Balanced NPK with micronutrients.',
                'prevention': 'Good drainage, avoid over-irrigation, crop rotation.',
                'water_requirement': 'Controlled irrigation, avoid waterlogging'
            }
        },
        'Banana': {
            'Panama Disease': {
                'description': 'Panama disease is caused by Fusarium oxysporum f.sp. cubense.',
                'symptoms': 'Yellowing and wilting of older leaves, splitting of pseudostem.',
                'causes': 'Soil-borne fungus, warm temperatures (25-30°C).',
                'pesticide': 'Use biocontrol agents like Trichoderma spp.',
                'fertilizer': 'Balanced NPK with emphasis on potassium.',
                'prevention': 'Use disease-free planting material, crop rotation.',
                'water_requirement': 'Maintain adequate moisture, avoid waterlogging'
            }
        }
    }
    
    disease_info = {}
    if crop_name in disease_db and disease_name in disease_db[crop_name]:
        disease_info = disease_db[crop_name][disease_name]
        disease_info['crop_name'] = crop_name
        disease_info['disease_name'] = disease_name
    else:
        disease_info = {
            'error': 'Please select a crop and disease',
            'crop_name': crop_name,
            'disease_name': disease_name
        }
    
    return render_template('disease.html', disease_info=disease_info)

@app.route('/market', methods=['GET', 'POST'])
def market():
    if request.method == 'POST':
        session['market_data'] = {
            'crop_name': request.form.get('crop_name')
        }
        return redirect(url_for('thankyou'))
    
    crop_name = session.get('market_data', {}).get('crop_name')
    if not crop_name:
        crop_name = session.get('crop_data', {}).get('crop_name')
    
    # Market price data
    market_prices = {
        'Rice': {'price': 28, 'unit': 'kg', 'trend': 'Stable', 'market': 'Local Market, Chennai'},
        'Wheat': {'price': 24, 'unit': 'kg', 'trend': 'Increasing', 'market': 'Regional Market, Delhi'},
        'Maize': {'price': 20, 'unit': 'kg', 'trend': 'Stable', 'market': 'Local Market, Mumbai'},
        'Cotton': {'price': 600, 'unit': 'quintal', 'trend': 'Increasing', 'market': 'Cotton Market, Surat'},
        'Sugarcane': {'price': 350, 'unit': 'quintal', 'trend': 'Stable', 'market': 'Sugar Mill, Pune'},
        'Groundnut': {'price': 85, 'unit': 'kg', 'trend': 'Decreasing', 'market': 'Local Market, Rajkot'},
        'Tomato': {'price': 40, 'unit': 'kg', 'trend': 'Increasing', 'market': 'Vegetable Market, Bangalore'},
        'Onion': {'price': 35, 'unit': 'kg', 'trend': 'Stable', 'market': 'Local Market, Nashik'},
        'Banana': {'price': 45, 'unit': 'kg', 'trend': 'Stable', 'market': 'Fruit Market, Coimbatore'},
        'Millets': {'price': 55, 'unit': 'kg', 'trend': 'Increasing', 'market': 'Organic Market, Hyderabad'}
    }
    
    price_data = market_prices.get(crop_name, {})
    price_data['crop_name'] = crop_name
    
    return render_template('market.html', price_data=price_data)

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists('database.db'):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)