import os
import requests
from gtts import gTTS
import pygame
import speech_recognition as sr
from translate import Translator

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
        else:
            return "Sorry, I couldn't fetch the weather data right now."
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {e}"

def get_agri_news(api_key):
    news_url = f"https://newsapi.org/v2/everything?q=agriculture&apiKey={api_key}&pageSize=5"
    
    try:
        response = requests.get(news_url)
        response.raise_for_status()  # Will raise an exception for HTTP errors
        news_data = response.json()
        
        # Debugging: Print the entire response data
        print("News API response:", news_data)
        
        if news_data["status"] == "ok":
            if news_data["totalResults"] > 0:
                headlines = [article["title"] for article in news_data["articles"]]
                return "Here are today's agriculture news headlines: " + ", ".join(headlines)
            else:
                return "No agriculture news found at the moment."
        else:
            return f"Error fetching news: {news_data.get('message', 'Unknown error')}"
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
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
    except Exception as e:
        print(f"Error recognizing speech: {e}")
    return None

def get_crop_suggestions(pH, soil_moisture):
    crop_suggestions = []
    
    if 6.0 <= pH <= 7.5 and soil_moisture > 30:
        crop_suggestions.append("Rice")
    if 5.5 <= pH <= 7.0 and soil_moisture > 20:
        crop_suggestions.append("Wheat")
    if 6.0 <= pH <= 6.5 and soil_moisture > 15:
        crop_suggestions.append("Maize")
    if 6.5 <= pH <= 7.5 and soil_moisture > 25:
        crop_suggestions.append("Sugarcane")
    if 5.0 <= pH <= 6.0 and soil_moisture > 20:
        crop_suggestions.append("Cotton")
    if 6.0 <= pH <= 7.5 and soil_moisture > 15:
        crop_suggestions.append("Tomato")
    
    if not crop_suggestions:
        return "No suitable crops found for the given pH and soil moisture values."
    
    return f"Based on the pH value of {pH} and soil moisture of {soil_moisture}%, you can grow: " + ", ".join(crop_suggestions) + "."

if _name_ == "_main_":
    language_map = {
        'tamil': 'ta',
        'hindi': 'hi',
        'english': 'en'
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
                    api_key = 'a3e1f560c3703832f3622fc38aa221e2'
                    weather_report = get_weather(api_key, city_name)
                    
                    translated_weather_report = translate_text(weather_report, preferred_language_code)
                    weather_report_file = 'weather_report.mp3'
                    convert_text_to_speech(translated_weather_report, weather_report_file, lang=preferred_language_code)
                    play_audio(weather_report_file)

                    news_prompt = translate_text("Would you like to hear today's agriculture news? Please say Yes or No.", preferred_language_code)
                    news_prompt_file = 'news_prompt.mp3'
                    convert_text_to_speech(news_prompt, news_prompt_file, lang=preferred_language_code)
                    news_response = recognize_speech(news_prompt_file)
                    
                    if news_response:
                        if "yes" in news_response.lower():
                            news_api_key = '305454260366475ebd761edc57e0e1c4'
                            agri_news = get_agri_news(news_api_key)
                            
                            translated_agri_news = translate_text(agri_news, preferred_language_code)
                            agri_news_file = 'agri_news.mp3'
                            convert_text_to_speech(translated_agri_news, agri_news_file, lang=preferred_language_code)
                            play_audio(agri_news_file)
                        else:
                            no_news_response = translate_text("Alright, no news today. Thank you for using our service.", preferred_language_code)
                            no_news_file = 'no_news.mp3'
                            convert_text_to_speech(no_news_response, no_news_file, lang=preferred_language_code)
                            play_audio(no_news_file)
                    else:
                        print("Response for news prompt not recognized.")
                
                pH_prompt = translate_text("Please say the pH value of the soil.", preferred_language_code)
                pH_prompt_file = 'pH_prompt.mp3'
                convert_text_to_speech(pH_prompt, pH_prompt_file, lang=preferred_language_code)
                pH_value_str = recognize_speech(pH_prompt_file)
                
                soil_moisture_prompt = translate_text("Please say the soil moisture percentage.", preferred_language_code)
                soil_moisture_prompt_file = 'soil_moisture_prompt.mp3'
                convert_text_to_speech(soil_moisture_prompt, soil_moisture_prompt_file, lang=preferred_language_code)
                soil_moisture_value_str = recognize_speech(soil_moisture_prompt_file)
                
                if pH_value_str and soil_moisture_value_str:
                    try:
                        pH_value = float(pH_value_str)
                        soil_moisture_value = float(soil_moisture_value_str)
                        
                        crop_suggestions = get_crop_suggestions(pH_value, soil_moisture_value)
                        translated_crop_suggestions = translate_text(crop_suggestions, preferred_language_code)
                        crop_suggestions_file = 'crop_suggestions.mp3'
                        convert_text_to_speech(translated_crop_suggestions, crop_suggestions_file, lang=preferred_language_code)
                        play_audio(crop_suggestions_file)
                    except ValueError:
                        error_message = translate_text("Invalid pH or soil moisture value.", preferred_language_code)
                        error_file = 'error.mp3'
                        convert_text_to_speech(error_message, error_file, lang=preferred_language_code)
                        play_audio(error_file)
                else:
                    print("pH or soil moisture value not recognized.")
                
            except Exception as e:
                print(f"Error in translation or weather fetching: {e}")
        else:
            print("Language not recognized or not supported.")
    else:
        print("Language not recognized.")
