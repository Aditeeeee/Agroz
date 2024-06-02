from flask import Flask, redirect, render_template, request, redirect, url_for, flash,session,jsonify
from werkzeug.utils import secure_filename
import os
import numpy as np
import requests
import pickle
import hashlib
import tensorflow
from mysql.connector import pooling
from keras.src.utils.image_utils import load_img
from keras.src.utils.image_utils import img_to_array
from keras.src.saving.saving_api import load_model
from keras.src.engine.sequential import Sequential
from keras.src.layers.activation.softmax import Softmax
import pandas as pd
from Fertilizer_Recommendations import fertilizer_dict
import json
from datetime import date
from sklearn.preprocessing import LabelEncoder  
import xgboost
from flask_cors import CORS
import logging



#Creating app
app = Flask(__name__)
app.secret_key = 'WeAreUnique#1289'
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)



# DATABASE
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    # "password": "shivani",
    "database": "Agrozz"
}

# Database connection pool
db_pool = pooling.MySQLConnectionPool(pool_name="my_pool", pool_size=5, **DB_CONFIG)



#LANDING PAGE
@app.route('/')
def landing_page():
    return render_template('Landing.html')



#SIGNUP
@app.route('/SignUp')
def sign_up():
    return render_template('SignUp.html')

# Function to hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/handles_signup', methods=['POST'])
def user_signup():
    try:
        data = request.form
        username = data['username']
        email = data['email']
        password = data['password']
        confirm_password = data['confirm_password']

        if password != confirm_password:
            error_pass = "Password and confirm password do not match"
            return render_template('SignUp.html',error_pass=error_pass)

        hashed_password = hash_password(password)

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM signup WHERE username=%s AND email=%s AND password=%s ",(username,email,hashed_password))
            same = cursor.fetchone()

        if same:  
                serror = "User already Exists!!"
                return render_template('SignUp.html',serror=serror)    

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO signup (username, email, password) VALUES (%s, %s, %s)",
                           (username, email, hashed_password))
            conn.commit()
            return render_template('Login.html')
    except Exception as e:
        return str(e)



#LOGIN
@app.route('/Login')
def login(): 
    return render_template('Login.html')

# Function to verify password
def verify_password(hashed_password, password):
    return hashed_password == hashlib.sha256(password.encode()).hexdigest()

@app.route('/handles_login', methods=['POST'])
def user_login():
    try:
        data = request.form
        email = data['email']
        password = data['password']

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, password FROM signup WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user and verify_password(user[1], password):
                session['user_id'] = user[0]  
                flash('Login successfully!.', 'success')
                return redirect(url_for('AOhome_page'))
            else:
                error_message = "Invalid email or password. Please check your credentials."
                return render_template('Login.html',error_message=error_message)
    except Exception as e:
        return str(e)
    


#FORGET PASSWORD    
@app.route('/forgot_password')
def f_password():
    return render_template('Forgot_Password.html')    

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.form
        email = data['email']
 
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM signup WHERE email=%s",(email,))
            user = cursor.fetchone()

        if user:
            return render_template('Reset_Password.html',email=email)  
        else:
            error_msg = "Email doesnot exist!!"
            return render_template('Forgot_Password.html',error_msg=error_msg)  



#RESET PASSWORD
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        data = request.form
        email = data['email']
        password = data['password']
        confirm_password = data['confirm_password']

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM signup WHERE email=%s",(email,))
            user = cursor.fetchone()

        if user and verify_password(user[0], password):
            error = "Password Already Exists!!"
            return render_template('Reset_Password.html',error=error)

        if password != confirm_password:
            error_pass = "Password and confirm password do not match"
            return render_template('Reset_Password.html',error_pass=error_pass)

        hashed_password = hash_password(password)

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE signup SET password=%s WHERE email=%s", (hashed_password,email))
            conn.commit()

        flash('Password updated successfully.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')
    



# NEW AND ARTICLES RELATED TO AGRICLUTURE [OUTSIDE]
NEWS_API_KEY = '6aa6772d26eb493f88de95af04af1818'  # Replace with your actual News API key

@app.route('/News_Articles')
def get_news_page():
    return render_template('News_Articles.html')

@app.route('/get_news')
def get_news():
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': '(indian agriculture OR indian farming OR indian crop OR crop selection OR fertilizer usage OR pests OR pesticides OR fertilizers OR manures OR cultivation OR irrigation OR soil health OR organic farming OR Agriculture subsidies) AND (Farming)',  # Keywords related to agriculture and India
        'language': 'en',  # Language of the articles (English)
        'sortBy': 'publishedAt',  # Sort by publication date
        'apiKey': NEWS_API_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        news_data = response.json()
        return jsonify(news_data)
    else:
        return jsonify({'error': 'Failed to fetch news'}), 500
    


#AGRICULTURAL OFFICER HOME PAGE
@app.route('/AO')
def AOhome_page():
    return render_template('AO_HomePage.html')



# NEW AND ARTICLES RELATED TO AGRICLUTURE [INSIDE]
@app.route('/Articles')
def news():
    return render_template('Articles_in.html')



#ADD FARMER
@app.route('/Add_NewFarmer')
def add_newFarmer():
    return render_template('Add_NewFarmer.html')

#Save Farmers Details
@app.route('/handle_farmer_details', methods=['POST'])
def handle_farmer_details():
   try:
        if request.method == 'POST':
            user_id = session.get('user_id')

            if user_id is None:
               return 'User not logged in'

            # Get form data
            name = request.form['name']
            phone = request.form['phone']
            taluka = request.form['taluka']
            revenue_village = request.form['revenue_village']
            village_panchayat = request.form['village_panchayat']
            ward = request.form['ward']
            # survey_no = request.form['survey_no']
            location_description = request.form['location_description']
            # crops_grown = request.form['crops_grown']
            # crops_proposed = request.form['crops_proposed']
            category = request.form['category']
            analysis_required = request.form['analysis_required']
            aadhaar_no = request.form['aadhaar_no']
            # registration_no = request.form['registration_no']
            area = request.form['area']
            
            with db_pool.get_connection() as conn:
               cursor = conn.cursor()
               cursor.execute("SELECT phone FROM farmers WHERE phone=%s",(phone,))
               user = cursor.fetchone()

               cursor.execute("SELECT aadhaar_no FROM farmers WHERE aadhaar_no=%s",(aadhaar_no,))
               user1 = cursor.fetchone()

               cursor.execute("SELECT * FROM farmers WHERE name=%s AND phone=%s AND taluka=%s AND revenue_village=%s AND village_panchayat=%s AND ward=%s AND location_description=%s AND category=%s AND analysis_required=%s AND aadhaar_no=%s AND area=%s",(name,phone,taluka,revenue_village,village_panchayat,ward,location_description,category,analysis_required,aadhaar_no,area))
               same = cursor.fetchone()

            if same:  
                serror = "Farmer already Exists!!"
                return render_template('Add_NewFarmer.html',serror=serror) 

            perror = None
            aerror = None   

            if user:
                perror = "Phone Number already Exist!!"
                
            if user1:    
                aerror = "Aadhar Number already Exist!!"
                
            if perror and aerror:     
                return render_template('Add_NewFarmer.html',aerror=aerror,perror=perror,name=name,taluka=taluka,revenue_village=revenue_village,village_panchayat=village_panchayat,ward=ward,location_description=location_description,category=category,analysis_required=analysis_required,area=area)
            elif perror:
                return render_template('Add_NewFarmer.html',perror=perror,name=name,taluka=taluka,revenue_village=revenue_village,village_panchayat=village_panchayat,ward=ward,location_description=location_description,category=category,analysis_required=analysis_required,aadhaar_no=aadhaar_no,area=area)
            elif aerror:
                return render_template('Add_NewFarmer.html',aerror=aerror,name=name,phone=phone,taluka=taluka,revenue_village=revenue_village,village_panchayat=village_panchayat,ward=ward,location_description=location_description,category=category,analysis_required=analysis_required,area=area)     
            else:
             with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                sql = "INSERT INTO farmers (user_id,name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (user_id,name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area)
                cursor.execute(sql, val)
                conn.commit()
                flash("Farmer successfully added!!",'success')
                return redirect(url_for('add_newFarmer'))
   except Exception as e:
        return f"An error occurred: {str(e)}"
   


#FARMERS LIST
@app.route('/Farmer_List')
def farmer_list():
    try:
        user_id = session.get('user_id')
       
        if user_id is None:
            return 'User not logged in'

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT farmer_id,name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area FROM farmers WHERE user_id = %s", (user_id,))
            farmer_details = cursor.fetchall()

        return render_template('FarmersList.html', farmer_details=farmer_details)
    
    except Exception as e:
        return str(e)       

#Search
@app.route('/search',methods = ['GET'])
def search():
    data = request.args.get('data')

    try:
     with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        if not data:
                cursor.execute("SELECT farmer_id,name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area FROM farmers")
                results = cursor.fetchall()
        else:
                cursor.execute("SELECT farmer_id,name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area FROM farmers WHERE name LIKE %s", ('%' + data + '%',))
                results = cursor.fetchall()
        return render_template('FarmersList.html', data=data,farmer_details=results) 
    except Exception as e:
        return f"An error occurred: {str(e)}"
    


#USER{AO} LOGOUT
@app.route('/logout')
def logout():
    session.pop('user_id', None)  
    return render_template('Landing.html')



#FARMER'S PAGE
@app.route('/Home')
def home_page():
    return render_template('Home.html')
  
#FARMER'S PROFILE
@app.route('/farmer/<int:farmer_id>')
def farmer_entry(farmer_id):
        if 'user_id' in session:
            session['farmer_id'] = farmer_id
            
            try:
                with db_pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM crop WHERE farmer_id = %s", (farmer_id,))
                    crop_history = cursor.fetchall()

                    cursor.execute("SELECT * FROM fertilizer WHERE farmer_id = %s", (farmer_id,))
                    fertilizer_history = cursor.fetchall()
                
                    processed_farmer_fertilizer = []
                    for row in fertilizer_history:
                        processed_row = []
                        for item in row:
                            if isinstance(item, bytes):  
                                item = item.decode('utf-8')  
                            processed_row.append(item)
                        processed_farmer_fertilizer.append(processed_row)

                    cursor.execute("SELECT * FROM chemfertilizer WHERE farmer_id = %s", (farmer_id,))
                    Chemfertilizer_history = cursor.fetchall()

                    cursor.execute("SELECT * FROM pesticide WHERE farmer_id = %s", (farmer_id,))
                    pesticide_history = cursor.fetchall()
                    
                    cursor.execute("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))
                    farmer_details = cursor.fetchone()
                    
                    if farmer_details:
                        cursor.execute("SHOW COLUMNS FROM farmers")
                        columns = [column[0] for column in cursor.fetchall()]

                        farmer_dict = {columns[i]: farmer_details[i] for i in range(len(columns))}
                    
                    return render_template('Home.html', columns=columns,crop_history=crop_history, fertilizer_history=processed_farmer_fertilizer, farmer_details=farmer_dict,Chemfertilizer_history=Chemfertilizer_history,pesticide_history=pesticide_history)
            except Exception as e:
                return f"An error occurred: {str(e)}"
                
        else:
            return redirect(url_for('login'))


#EDIT PROFILE
@app.route('/edit_profile/<int:farmer_id>')
def edit_profile(farmer_id):
    try:
        # Fetch farmer details from the database
        with db_pool.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))
            farmer_details = cursor.fetchone()

        return render_template('EditProfile.html', farmer_details=farmer_details)
    except Exception as e:
        return f"An error occurred: {str(e)}"

#UPDATE PROFILE IN DATABASE
@app.route('/update_profile/<int:farmer_id>', methods=['POST'])
def update_profile(farmer_id):
    try:
        if request.method == 'POST':
            # Get form data
            name = request.form['name']
            phone = request.form['phone']
            taluka = request.form['taluka']
            revenue_village = request.form['revenue_village']
            village_panchayat = request.form['village_panchayat']
            ward = request.form['ward']
            # survey_no = request.form['survey_no']
            location_description = request.form['location_description']
            # crops_grown = request.form['crops_grown']
            # crops_proposed = request.form['crops_proposed']
            category = request.form['category']
            analysis_required = request.form['analysis_required']
            aadhaar_no = request.form['aadhaar_no']
            registration_no = request.form['registration_no']
            area = request.form['area']
            
            # Update profile data in the database
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                sql = "UPDATE farmers SET name=%s, phone=%s, taluka=%s, revenue_village=%s, village_panchayat=%s, ward=%s, location_description=%s, category=%s, analysis_required=%s, aadhaar_no=%s, area=%s WHERE farmer_id=%s"
                val = (name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area, farmer_id)               
                cursor.execute(sql, val)
                conn.commit()

            # Redirect to the farmer's profile page after updating
            return redirect(url_for('farmer_entry', farmer_id=farmer_id))
    except Exception as e:
        return f"An error occurred: {str(e)}"

#DELETE FARMER
@app.route('/delete/<int:farmer_id>')
def delete(farmer_id):
    try:
        # Fetch farmer details from the database
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM farmers WHERE farmer_id = %s", (farmer_id,))
            conn.commit()

        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT farmer_id,name, phone, taluka, revenue_village, village_panchayat, ward, location_description, category, analysis_required, aadhaar_no, area FROM farmers")
            farmer_details = cursor.fetchall()    

        return render_template('FarmersList.html',farmer_details=farmer_details)
    except Exception as e:
        return f"An error occurred: {str(e)}"    



#FARMER'S LOGOUT
@app.route('/logoutFarmer')
def logout2():
    session.pop('farmer_id', None)
    return render_template('AO_HomePage.html')


#RECOMMENDATIONS
@app.route('/recommendation')
def recom():
    return render_template('Recommendations.html')



#CROP RECOMMENDATION
#import model
model = pickle.load(open('model/Crop/NaiveBayes_model.pkl','rb'))
df = pd.read_csv('data/Organic fertilizer data.csv')

#weather fetching
def weather_fetch(city_name):
    api_key = '49287276118b089ee94e7a10946443cf'

    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {'q': city_name, 'appid': api_key}

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            temperature = data['main']['temp'] - 273.15  # Convert temperature to Celsius
            humidity = data['main']['humidity']
            return temperature, humidity
        else:
            print(f"Failed to fetch weather data: {data['message']}")
            return None, None
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        return None, None
   
@app.route('/Crop')
def crop_recommendation():
    return render_template('Crop.html')

@app.route('/predict', methods=['POST'])
def predict():
    N = float(request.form['nitrogen'])
    P = float(request.form['phosphorus'])
    K = float(request.form['potassium'])
    ph = float(request.form['ph'])
    rainfall = float(request.form['rainfall'])
    city = request.form.get("city")

    temperature, humidity = weather_fetch(city)
    
    if temperature is not None and humidity is not None:
        data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        prediction = model.predict(data)
        crop_prediction = prediction[0]

        logging.info("Received input data:")
        logging.info(f"N: {N}, P: {P}, K: {K}, temperature: {temperature}, humidity: {humidity}, pH: {ph}, rainfall: {rainfall}")

        CROP_FOLDER = './static/crops'

        image_name = str(crop_prediction) + '.jpg'
        image_path = os.path.join(CROP_FOLDER, image_name)
        if os.path.exists(image_path):
        # Pass the image URL to the template
           image_url = url_for('static', filename='crops/' + image_name)
           print("Image URL:", image_url)

        # Insert recommendation data into the database
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO crop (farmer_id,nitrogen ,phosphorus, potassium, temperature,humidity,ph,rainfall,crop_prediction,recommendation_date ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               (session['farmer_id'],N ,P, K, temperature,humidity,ph,rainfall,str(crop_prediction),date.today()))
                conn.commit()
        except Exception as e:
            return f"An error occurred while saving recommendation: {str(e)}"

        logging.info("Predicted Crop:", crop_prediction) # Debugging statement

        # Render template with recommendation result
        return render_template('Crop_Result.html', predicted_crop=crop_prediction,image_url=image_url)
    else:
        print(f"Failed to fetch weather data for {city}") 



#ORGANIC FERTILIZER RECOMMENDATION
@app.route('/Fertilizer_Option_Page')
def fertilizerSection():
    return render_template('Fertilizer_Option_Page.html')

@app.route('/Fertilizer')
def fertilizer_recommendation():
    return render_template('Fertilizer.html')

@app.route('/predict_fertilizer', methods=['POST'])
def predict_fertilizer():
    try:
        N_input = int(request.form['nitrogen'])
        P_input = int(request.form['phosphorus'])
        K_input = int(request.form['potassium'])
        crop = str(request.form['cropName'])
    except ValueError:
        return "Error: Invalid input. Please enter numeric values for nitrogen, phosphorus, and potassium."

    try:
        df_crop = df[df['Crop'] == crop]
        N_desired = df_crop['N'].iloc[0]
        P_desired = df_crop['P'].iloc[0]
        K_desired = df_crop['K'].iloc[0]
    except IndexError:
        return "Error: Crop '{}' not found in the database.".format(crop)

    N_difference = N_desired - N_input
    P_difference = P_desired - P_input
    K_difference = K_desired - K_input

    recommendations = []

    # Handle Nitrogen recommendations
    if N_difference < 0:
        recommendations.append((fertilizer_dict['NHigh'], abs(N_difference)))
    elif N_difference > 0:
        recommendations.append((fertilizer_dict['Nlow'], abs(N_difference)))
    else:
        recommendations.append((fertilizer_dict['NNo'], 0))

    # Handle Phosphorus recommendations
    if P_difference < 0:
        recommendations.append((fertilizer_dict['PHigh'], abs(P_difference)))
    elif P_difference > 0:
        recommendations.append((fertilizer_dict['Plow'], abs(P_difference)))
    else:
        recommendations.append((fertilizer_dict['PNo'], 0))

    # Handle Potassium recommendations
    if K_difference < 0:
        recommendations.append((fertilizer_dict['KHigh'], abs(K_difference)))
    elif K_difference > 0:
        recommendations.append((fertilizer_dict['Klow'], abs(K_difference)))
    else:
        recommendations.append((fertilizer_dict['KNo'], 0))

    # Convert recommendations list to JSON string
    recommendations_json = json.dumps(recommendations)

    # Extract individual recommendations for N, P, and K
    recommendation_N = None
    recommendation_P = None
    recommendation_K = None
    for recommendation, difference in recommendations:
        if "Nitrogen" in recommendation["title"]:
            recommendation_N = recommendation["description"] + '\n' + '\n'.join(map(str, recommendation["items"]))
        elif "Phosphorus" in recommendation["title"]:
            recommendation_P = recommendation["description"] + '\n' + '\n'.join(map(str, recommendation["items"]))
        elif "Potassium" in recommendation["title"]:
            recommendation_K = recommendation["description"] + '\n' + '\n'.join(map(str, recommendation["items"]))

    # Insert data into the database
    try:
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            # Insert input values, crop name, recommendations, and timestamp into the database table
            cursor.execute("INSERT INTO fertilizer (farmer_id, crop, nitrogen, phosphorus, potassium, recommendation_N, recommendation_P, recommendation_K,recommendation_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)",
                        (session['farmer_id'], crop, N_input, P_input, K_input, recommendation_N, recommendation_P, recommendation_K,date.today()))
            conn.commit()
    except Exception as e:
        return f"An error occurred while inserting data into the database: {str(e)}"

    return render_template('Fertilizer_Result.html', recommendations=recommendations)



#CHEMICAL FERTILIZER RECOMMENDATION
@app.route('/ChemicalFertilizer')
def chemical_fertilizer_recommendation():
    return render_template('Chemical_Fertilizer.html')

#import model
with open('model/Fertilizer/xgboost_model.pkl', 'rb') as file:
    xgboost_model = pickle.load(file)

#import model
with open('model/Fertilizer/label_encoder.pkl', 'rb') as file:
    label_encoder = pickle.load(file)

@app.route('/predictChemicalFertilizer', methods=['POST'])
def predictChemicalFertilizer():
    try:
        # Get user input from the form
        N = int(request.form['N'])
        P = int(request.form['P'])
        K = int(request.form['K'])
        Crop = request.form['Crop']
        
        # Create a DataFrame with the user input
        input_data = pd.DataFrame([[N, P, K, Crop]], columns=['N', 'P', 'K', 'Crop'])

        # Make prediction using the loaded model
        prediction = xgboost_model.predict(input_data)  

        # Decode the numerical prediction to get the fertilizer name
        predicted_fertilizer = label_encoder.inverse_transform(prediction)[0]
        fertilizer_predicted = label_encoder.inverse_transform(prediction)

        FERTILIZER_FOLDER = './static/fertilizers'

        image_name = str(predicted_fertilizer) + '.jpg'
        image_path = os.path.join(FERTILIZER_FOLDER, image_name)
        if os.path.exists(image_path):
        # Pass the image URL to the template
           image_url = url_for('static', filename='fertilizers/' + image_name)

        try:
         with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            # Insert input values, crop name, recommendations, and timestamp into the database table
            cursor.execute("INSERT INTO Chemfertilizer (farmer_id, crop, nitrogen, phosphorus, potassium, recommendation,recommendation_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (session['farmer_id'], Crop, N, P, K,str(predicted_fertilizer),date.today()))
            conn.commit()
        except Exception as e:
            return f"An error occurred while inserting data into the database: {str(e)}"

        # Render the result page with the prediction
        return render_template('Chemical_Fertilizer_Result.html', prediction_text=fertilizer_predicted[0],image_url=image_url)
    except Exception as e:
        return f"An error occurred: {str(e)}"        
    


#PESTICIDE RECOMMENDATION    
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model/Pesticide')

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG'}

MODEL = load_model(os.path.join(MODEL_DIR, 'PLANT_DISEASE.h5'))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLASSES = ['Apple scab', 'Apple Black rot', 'Apple Cedar apple rust', 'Apple healthy', 'Blueberry healthy', 'Cherry (including sour) Powdery mildew', 'Cherry (including sour) healthy', 'Corn (maize) Cercospora leaf spot Gray leaf spot', 'Corn(maize) Common rust', 'Corn(maize) Northern Leaf Blight', 'Corn(maize) healthy', 'Grape Black rot', 'Grape Esca(Black Measles)', 'Grape Leaf blight(Isariopsis Leaf Spot)', 'Grape healthy', 'Orange Haunglongbing(Citrus greening)', 'Peach Bacterial spot', 'Peach healthy', 'Bell PepperBacterial_spot', 'Pepper bell healthy', 'Potato Early blight', 'Potato Late blight', 'Potato healthy', 'Raspberry healthy', 'Soybean healthy', 'Squash Powdery mildew', 'Strawberry Leaf scorch', 'Strawberry healthy', 'Tomato Bacterial spot', 'Tomato Early blight', 'Tomato Late blight', 'Tomato Leaf Mold', 'Tomato Septoria leaf spot', 'Tomato Spider mites (Two-spotted spider mite)', 'Tomato Target Spot', 'Tomato Yellow Leaf Curl Virus', 'Tomato mosaic virus', 'Tomato healthy']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


PESTICIDE_FOLDER = './static/Pesticide'

@app.route('/plantdisease/<res>')
def plantresult(res):
    print(res)
    corrected_result = ""
    for i in res:
        if i != '_':
            corrected_result = corrected_result + i

      # Check if an image exists for the predicted disease
    image_name = corrected_result + '.jpg'
    image_path = os.path.join(PESTICIDE_FOLDER, image_name)
    if os.path.exists(image_path):
        # Pass the image URL to the template
        image_url = url_for('static', filename='Pesticide/' + image_name)

        try:
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO pesticide (farmer_id,Pest,recommendation_date ) VALUES (%s, %s, %s)",
                               (session['farmer_id'],corrected_result,date.today()))
                conn.commit()
        except Exception as e:
            return f"An error occurred while saving recommendation: {str(e)}"
        return render_template('pesticideResult.html', corrected_result=corrected_result, image_url=image_url)
    else:
        return render_template('pesticideResult.html', corrected_result=corrected_result)


@app.route('/plantdisease', methods=['GET', 'POST'])
def plantdisease():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            model = MODEL
            imagefile = tensorflow.keras.utils.load_img(os.path.join(app.config['UPLOAD_FOLDER'], filename), target_size=(224, 224, 3))
            input_arr = tensorflow.keras.preprocessing.image.img_to_array(imagefile)
            input_arr = np.array([input_arr])
            probability_model = tensorflow.keras.Sequential([model, 
                                         tensorflow.keras.layers.Softmax()])
            predict = probability_model.predict(input_arr)
            p = np.argmax(predict[0])
            res = CLASSES[p]
            print(res)
            return redirect(url_for('plantresult', res=res))
    return render_template("Pesticide.html")
    
#main
if __name__ == '__main__':
    app.run(debug=True)