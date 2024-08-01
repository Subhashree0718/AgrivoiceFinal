import firebase_admin
from firebase_admin import credentials, firestore
import speech_recognition as sr
import pyttsx3
import requests
from googletrans import Translator

# Initialize Firebase
try:
    cred = credentials.Certificate("C:/Users/Vishal V D/OneDrive/Desktop/Python chatbot/firebase.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit()

# Initialize Speech Recognition and Text-to-Speech
recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()
translator = Translator()

# Weather API Key
API_KEY = '792cf67f483f977ee5a8225bbccbc1c8'

def get_weather(city):
    try:
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
        response = requests.get(base_url, params=params)
        data = response.json()

        if data['cod'] == 200:
            weather_description = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"The weather in {city} is {weather_description} with a temperature of {temp}°C."
        else:
            return f"Sorry, I couldn't get the weather information: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Error getting weather data: {e}"

def recognize_speech():
    with sr.Microphone() as source:
        print("Listening...")
        tts_engine.say("Listening...")
        tts_engine.runAndWait()
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that."
        except sr.RequestError as e:
            return f"Sorry, there was a problem with the request: {e}"

def text_to_speech(text, lang='en'):
    try:
        translated_text = translator.translate(text, dest=lang).text if lang != 'en' else text
        print(translated_text)
        if lang == 'ta':
            tts_engine.setProperty('voice', 'com.apple.speech.synthesis.voice.lekha')  # Example for Tamil voice
        else:
            tts_engine.setProperty('voice', 'com.apple.speech.synthesis.voice.Alex')  # Example for English voice
        tts_engine.say(translated_text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"Error in text-to-speech: {e}")

def detect_language(text):
    return translator.detect(text).lang

def chatbot_response(user_input, lang='en'):
    user_input = user_input.lower()

    try:
        qa_pairs = get_all_qa_pairs()
    except Exception as e:
        return f"Error fetching QA pairs: {e}"

    for qa in qa_pairs:
        if qa['question'].lower() in user_input:
            return qa['answer']

    if "weather" in user_input:
        city = extract_city_from_input(user_input)
        if city:
            return get_weather(city)
        else:
            return "Please provide a valid city name to get the weather information."

    return "I don't understand that question."

def extract_city_from_input(user_input):
    parts = user_input.split("in")
    if len(parts) > 1:
        return parts[-1].strip()
    return None

def get_all_qa_pairs():
    qa_pairs = []
    try:
        docs = db.collection('chatbot').stream()
        for doc in docs:
            qa_pairs.append(doc.to_dict())
    except Exception as e:
        print(f"Error fetching documents: {e}")
    return qa_pairs

def store_in_firebase(question, answer):
    try:
        doc_ref = db.collection('chatbot').document()
        doc_ref.set({
            'question': question,
            'answer': answer
        })
        print(f"Stored question: {question}, answer: {answer}")
    except Exception as e:
        print(f"Error storing QA pair: {e}")

def add_weather_questions():
    weather_questions = [
        {"question": "What is the temperature in New York?", "answer": "Please provide the city name to get the temperature."},
        {"question": "Will it rain today?", "answer": "Please provide the city name to check if it will rain today."},
        {"question": "How is the weather in London?", "answer": "Please provide the city name to get the weather information."},
        {"question": "Is it sunny in Tokyo?", "answer": "Please provide the city name to get the weather information."}
    ]

    existing_questions = [qa['question'] for qa in get_all_qa_pairs()]
    for qa in weather_questions:
        if qa['question'] not in existing_questions:
            store_in_firebase(qa['question'], qa['answer'])

def main():
    add_weather_questions()

    while True:
        user_input = recognize_speech()

        if user_input:
            detected_language = detect_language(user_input)
            response = chatbot_response(user_input, detected_language)
            print(f"Response: {response}")
            text_to_speech(response, detected_language)

if _name_ == "_main_":
    main()
