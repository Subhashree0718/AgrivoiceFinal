import os
import requests
from gtts import gTTS
import pygame
import speech_recognition as sr
from translate import Translator
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate(r"C:\Users\SHRUTHI V\OneDrive\Desktop\sketch_aug2aagrivoice\agrivoice\agrivoice-590d4-firebase-adminsdk-810fu-b66fbe7707.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Constants for conversion (example values)
NITROGEN_CONVERSION_FACTOR = 100  # Adjust as per sensor calibration
PHOSPHORUS_CONVERSION_FACTOR = 80  # Adjust as per sensor calibration
POTASSIUM_CONVERSION_FACTOR = 60    # Adjust as per sensor calibration

def translate_text(text, target_language):
    translator = Translator(to_lang=target_language)
    return translator.translate(text)

def get_weather(api_key, location):
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
    
    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json()
        
        if weather_data["cod"] == 200:
            main = weather_data["main"]
            weather_desc = weather_data["weather"][0]["description"]
            temperature = main["temp"] - 273.15
            return f"The current temperature in {location} is {temperature:.2f}°C with {weather_desc}."
        return "Sorry, I couldn't fetch the weather data right now."
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {e}"

def get_agri_news(api_key):
    news_url = f"https://api.currentsapi.services/v1/search?keywords=agriculture&apiKey={api_key}"
    
    try:
        response = requests.get(news_url)
        response.raise_for_status()
        news_data = response.json()
        
        if news_data["status"] == "ok" and news_data["news"]:
            headlines = [article["title"] for article in news_data["news"]]
            return "Here are today's agriculture news headlines: " + ", ".join(headlines)
        return "No agriculture news found at the moment."
    except requests.exceptions.RequestException as e:
        return f"Error fetching news data: {e}"

def convert_text_to_speech(text, output_file, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(output_file)
        print(f"Audio content written to file: {output_file}")
    except Exception as e:
        print(f"Error converting text to speech: {e}")

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def recognize_speech(prompt_file=None):
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            if prompt_file:
                play_audio(prompt_file)
            print("Adjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = recognizer.listen(source)
            print("Recognizing...")
            response = recognizer.recognize_google(audio)
            print(f"Recognized: {response}")  # Debug print
            return response
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        print(f"Error recognizing speech: {e}")
    
    return None

def get_real_time_sensor_data():
    """Fetch the latest sensor values from Firebase."""
    try:
        sensor_data_ref = db.collection('sensorData').document('latest')
        sensor_data = sensor_data_ref.get()
        if sensor_data.exists:
            data = sensor_data.to_dict()
            print("Fetched sensor data from Firestore:", data)  # Debug print
            return data
        else:
            print("No sensor data found.")
            return None
    except Exception as e:
        print(f"Error retrieving sensor data: {e}")
        return None

def convert_sensor_reading_to_ppm(reading, conversion_factor):
    return reading * conversion_factor / 4095  # Scale from 0-4095 to ppm

def suggest_manure(nitrogen, phosphorus, potassium):
    suggestions = []
    
    if nitrogen < 10:
        suggestions.append("Add nitrogen-rich manure like cow dung.")
    if phosphorus < 5:
        suggestions.append("Add phosphorus-rich manure like rock phosphate.")
    if potassium < 5:
        suggestions.append("Add potassium-rich manure like wood ash.")
    
    if not suggestions:
        return "No additional manure needed."
    
    return "Suggestions: " + ", ".join(suggestions)

def get_crop_suggestions(soil_moisture):
    crop_suggestions = []
    
    if soil_moisture > 30:
        crop_suggestions.append("Rice")
    if soil_moisture > 20:
        crop_suggestions.append("Wheat")
    if soil_moisture > 15:
        crop_suggestions.append("Maize")
    if soil_moisture > 25:
        crop_suggestions.append("Sugarcane")
    if soil_moisture > 20:
        crop_suggestions.append("Cotton")
    if soil_moisture > 15:
        crop_suggestions.append("Tomato")
    
    if not crop_suggestions:
        return "No suitable crops found for the given soil moisture values."
    
    return "Based on the soil moisture of {:.2f}%, you can grow: {}".format(soil_moisture, ", ".join(crop_suggestions))

if __name__ == "__main__":
    language_map = {
        'tamil': 'ta',
        'hindi': 'hi',
        'english': 'en',
        'malayalam': 'ml',
        'kannada': 'kn'
    }

    lang_prompt = 'prompt.mp3'
    convert_text_to_speech("Please say your preferred language.", lang_prompt, lang='en')
    preferred_language = recognize_speech(lang_prompt)
    
    if preferred_language:
        print(f"Preferred language: {preferred_language}")
        preferred_language_code = language_map.get(preferred_language.lower())
        
        if preferred_language_code:
            try:
                weather_prompt = translate_text("Please say the city name for the weather update.", preferred_language_code)
                weather_prompt_file = 'weather_prompt.mp3'
                convert_text_to_speech(weather_prompt, weather_prompt_file, lang=preferred_language_code)
                city_name = recognize_speech(weather_prompt_file)
                
                if city_name:
                    print(f"City name: {city_name}")
                    api_key = 'a3e1f560c3703832f3622fc38aa221e2'  # Replace with your actual API key
                    weather_report = get_weather(api_key, city_name)
                    
                    translated_weather_report = translate_text(weather_report, preferred_language_code)
                    weather_report_file = 'weather_report.mp3'
                    convert_text_to_speech(translated_weather_report, weather_report_file, lang=preferred_language_code)
                    play_audio(weather_report_file)

                else:
                    print("City name not recognized.")
            except Exception as e:
                print(f"Error in processing: {e}")

            # Fetch real-time sensor data
            sensor_data = get_real_time_sensor_data()
            try:
                if sensor_data:
                    # Print all sensor data for debugging
                    print("Sensor data:", sensor_data)
                    
                    # Correctly map the Firestore keys to the variables
                    raw_nitrogen = sensor_data.get('pot1')
                    raw_phosphorus = sensor_data.get('pot2')
                    raw_potassium = sensor_data.get('pot3')
                    soil_moisture = sensor_data.get('moisture')

                    # Convert to ppm
                    nitrogen_ppm = convert_sensor_reading_to_ppm(raw_nitrogen, NITROGEN_CONVERSION_FACTOR)
                    phosphorus_ppm = convert_sensor_reading_to_ppm(raw_phosphorus, PHOSPHORUS_CONVERSION_FACTOR)
                    potassium_ppm = convert_sensor_reading_to_ppm(raw_potassium, POTASSIUM_CONVERSION_FACTOR)

                    # Debug prints
                    print(f"Nitrogen (ppm): {nitrogen_ppm:.2f}")
                    print(f"Phosphorus (ppm): {phosphorus_ppm:.2f}")
                    print(f"Potassium (ppm): {potassium_ppm:.2f}")
                    print(f"Soil Moisture: {soil_moisture}")

                    # Read out sensor values
                    sensor_values_text = (
                        f"Current sensor readings are: "
                        f"Nitrogen: {nitrogen_ppm:.2f} ppm, "
                        f"Phosphorus: {phosphorus_ppm:.2f} ppm, "
                        f"Potassium: {potassium_ppm:.2f} ppm, "
                        f"Soil Moisture: {soil_moisture if soil_moisture is not None else 'missing'}%."
                    )
                    translated_sensor_values_text = translate_text(sensor_values_text, preferred_language_code)
                    sensor_values_file = 'sensor_values.mp3'
                    convert_text_to_speech(translated_sensor_values_text, sensor_values_file, lang=preferred_language_code)
                    play_audio(sensor_values_file)

                    # Manure suggestions
                    manure_suggestions = suggest_manure(nitrogen_ppm, phosphorus_ppm, potassium_ppm)
                    translated_manure_suggestions = translate_text(manure_suggestions, preferred_language_code)
                    manure_suggestions_file = 'manure_suggestions.mp3'
                    convert_text_to_speech(translated_manure_suggestions, manure_suggestions_file, lang=preferred_language_code)
                    play_audio(manure_suggestions_file)

                    # Crop suggestions based on soil moisture
                    crop_suggestion = get_crop_suggestions(soil_moisture)
                    translated_crop_suggestion = translate_text(crop_suggestion, preferred_language_code)
                    crop_suggestion_file = 'crop_suggestion.mp3'
                    convert_text_to_speech(translated_crop_suggestion, crop_suggestion_file, lang=preferred_language_code)
                    play_audio(crop_suggestion_file)

                    # Fetch agriculture news
                    news_api_key = 'jZc6IFKMBZSsFhxiyVDsVKLVoxO4VyEw5JHU9p6ln868qo3P'  # Replace with your actual news API key
                    agri_news = get_agri_news(news_api_key)
                    translated_agri_news = translate_text(agri_news, preferred_language_code)
                    agri_news_file = 'agri_news.mp3'
                    convert_text_to_speech(translated_agri_news, agri_news_file, lang=preferred_language_code)
                    play_audio(agri_news_file)
            except Exception as e:
                print(f"Error retrieving or processing sensor data: {e}")
        else:
            print("Preferred language not supported.")
    else:
        print("Language not recognized.")
