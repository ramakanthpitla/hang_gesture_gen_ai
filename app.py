import streamlit as st
import requests
import speech_recognition as sr
import google.generativeai as genai
import googleapiclient.discovery

# Configure Streamlit Page
st.set_page_config(page_title="AI Recipe Maker", page_icon="🍽", layout="wide")
st.title("🍽 AI Recipe Maker")

# Function to recognize speech input
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak the dish name clearly.")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError:
            return "Speech recognition service is unavailable."
        except Exception as e:
            return str(e)

# Initialize session state for dish_name if not set
if "dish_name" not in st.session_state:
    st.session_state.dish_name = ""

# Search Box with Voice Button
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if st.button("🎤 Speak"):
        spoken_text = recognize_speech()
        if "Could not understand" not in spoken_text and "unavailable" not in spoken_text:
            st.session_state.dish_name = spoken_text
            st.rerun()

    dish_name = st.text_input("\U0001F50E Generate", st.session_state.dish_name, key="dish_name", 
                              help="Enter a dish name", 
                              placeholder="Type here...", 
                              max_chars=50)

    st.markdown("""
        <style>
            div[data-baseweb='input'] {
                border: 2px solid orange !important;
                border-radius: 10px;
                padding: 5px;
                text-align: center;
                font-size: 18px;
            }
        </style>
    """, unsafe_allow_html=True)

# API Key for Gemini AI (Replace with your actual key)
GEMINI_API_KEY = "AIzaSyAJgtms_E7FRqcc-AtvjOlmTQeu0h9_q1Y"

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Function to get recipe from TheMealDB API
def get_recipe(meal_name):
    api_url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={meal_name}"
    response = requests.get(api_url)
    data = response.json()

    if data.get("meals"):
        meal = data["meals"][0]
        recipe_name = meal["strMeal"]
        image_url = meal["strMealThumb"]
        ingredients = [meal[f"strIngredient{i}"] for i in range(1, 8) if meal[f"strIngredient{i}"]]
        instructions = meal["strInstructions"].split(". ")[:7]
        cautions = "Be cautious with cooking temperature and spice levels."
        return recipe_name, ingredients, instructions, image_url, cautions
    else:
        return None, None, None, None, None  # If not found, trigger AI generation

# Function to generate a structured recipe using Gemini AI
def generate_recipe_with_gemini(dish_name):
    prompt = f"Provide a structured recipe for {dish_name}, including a list of max 7 ingredients, max 7 step-by-step instructions, and a caution message. Format as follows: Ingredients: [list of ingredients] Instructions: [Step 1: ..., Step 2: ..., etc.] Caution: [caution message]"
    
    # Make sure you have your correct Gemini API key
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")   
        
        response = model.generate_content(prompt)
        response_text = response.candidates[0].content.parts[0].text.split("\n")
        
        ingredients = []
        instructions = []
        caution = ""
        section = None
        
        for line in response_text:
            line = line.strip()
            if line.lower().startswith("ingredients:"):
                section = "ingredients"
            elif line.lower().startswith("instructions:"):
                section = "instructions"
            elif line.lower().startswith("caution:"):
                section = "caution"
            elif section == "ingredients" and line and len(ingredients) < 7:
                ingredients.append(line)
            elif section == "instructions" and line and len(instructions) < 7:
                instructions.append(line)
            elif section == "caution" and line:
                caution = line
        
        return ingredients, instructions, caution
    except Exception as e:
        # Handle errors gracefully
        error_message = f"⚠ Error with Gemini AI: {str(e)}"
        print(error_message)  # Log the error for debugging
        return [error_message], [error_message], error_message

# Function to get YouTube video links related to the recipe
def get_youtube_videos(dish_name):
    youtube_api_key = "AIzaSyCUm_Jv5_B86ifCwm7UYDzUWRCObUyiwk0"
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=youtube_api_key)
    
    request = youtube.search().list(
        q=dish_name + " recipe",
        part="snippet",
        maxResults=2,  # Modify this if you need more results
        type="video"
    )
    
    response = request.execute()

    video_urls = []
    for item in response["items"]:
        video_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        video_urls.append(video_url)

    return video_urls

# Recipe Search (Text & Voice)
if dish_name:
    st.success(f"🔍 Searching for: {dish_name}")
    
    # Fetch recipe from TheMealDB
    meal_name, ingredients, instructions, image_url, cautions = get_recipe(dish_name)

    if meal_name:
        st.write(f"### 🍽 Recipe: {meal_name}")
        
        # Display image with reduced size
        st.image(image_url, caption=meal_name, use_column_width=True, width=400)  # Adjust 'width' as needed
        
        # Structured Format
        st.write("### 🥕 AI-Generated Ingredients")
        for ingredient in ingredients:
            st.write(f"- {ingredient}")
        
        st.write("### 🍳 AI-Generated Step-by-Step Instructions")
        for i, step in enumerate(instructions, start=1):
            st.write(f"*Step {i}:* {step}")
        
        st.write("### ⚠ AI-Generated Caution")
        st.write(cautions)
        
        # Fetch and display YouTube videos related to the dish
        st.write("### 🎥 Watch Related Videos")
        video_urls = get_youtube_videos(dish_name)
        for url in video_urls:
            video_id = url.split("v=")[-1]
            st.markdown(f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>', unsafe_allow_html=True)
    else:
        st.warning("❌ Recipe not found in TheMealDB. Generating one using AI...")
        
        # Generate structured recipe with Gemini
        ai_ingredients, ai_instructions, ai_caution = generate_recipe_with_gemini(dish_name)
        
        st.write("### 🥕 AI-Generated Ingredients")
        for ingredient in ai_ingredients:
            st.write(f"- {ingredient}")

        st.write("### 🍳 AI-Generated Step-by-Step Instructions")
        for i, step in enumerate(ai_instructions, start=1):
            st.write(f"*Step {i}:* {step}")

        st.write("### ⚠ AI-Generated Caution")
        st.write(ai_caution)
        
        # Fetch and display YouTube videos related to the dish
        st.write("### 🎥 Watch Related Videos")
        video_urls = get_youtube_videos(dish_name)
        for url in video_urls:
            video_id = url.split("v=")[-1]
            st.markdown(f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.write("Developed by [Your Name]")