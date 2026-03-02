from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import os
import speech_recognition as sr
from fuzzywuzzy import process
import pyttsx3

app = Flask(__name__)

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Load dataset
file_path = 'datasets/All_Recipes_Cleaned.csv'
full_path = os.path.abspath(file_path)
print("Looking for file at:", full_path)

if os.path.exists(full_path):
    try:
        df = pd.read_csv(full_path, encoding="ISO-8859-1")
        print("Dataset loaded successfully!")
    except Exception as e:
        print(f"Error loading the dataset: {e}")
        df = pd.DataFrame()  # Create an empty DataFrame to avoid crashes
else:
    print(f"Warning: The file {full_path} does not exist. Using an empty dataset.")
    df = pd.DataFrame()  # Create an empty DataFrame to avoid crashes

favorites = []

def speak_text(text):
    """Convert text to speech"""
    tts_engine.say(text)
    tts_engine.runAndWait()

def recognize_speech():
    """Uses voice recognition to get the dish name."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎙️ Say the dish name...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            dish_name = recognizer.recognize_google(audio)
            print(f"🗣️ You said: {dish_name}")
            return dish_name
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            print("⚠️ Unable to recognize speech. Try again.")
            return None

def get_recipe_details(dish_name, dietary_preference=None):
    """Find the best-matching recipe using fuzzy search, with optional dietary filtering."""
    filtered_df = df
    if dietary_preference:
        filtered_df = filtered_df[
            filtered_df["Dietary Preference"].str.contains(dietary_preference, case=False, na=False)]

    if filtered_df.empty:
        return f"❌ No recipes found for '{dish_name}' with dietary preference '{dietary_preference}'. Try again!", None

    all_dish_names = filtered_df["Food Name"].tolist()
    best_match, score = process.extractOne(dish_name, all_dish_names)

    if score < 80:
        return f"❌ No close match found for '{dish_name}'. Try again!", None

    filtered_recipe = filtered_df[filtered_df["Food Name"] == best_match].iloc[0]

    # Format the response
    response = f"\n🍽️ **{filtered_recipe['Food Name']}** (Best match for: {dish_name})\n"
    response += f"📌 **Category:** {filtered_recipe['Category']}\n"
    response += f"🥦 **Dietary Preference:** {filtered_recipe['Dietary Preference']}\n"
    response += f"📝 **Ingredients:** {filtered_recipe['Ingredients']}\n"
    response += f"👨‍🍳 **Cooking Instructions:** {filtered_recipe['Cooking Instructions']}\n"
    response += f"🌶️ **Spice Level:** {filtered_recipe['Spice Level']}\n"
    response += f"⏳ **Cooking Time:** {filtered_recipe['Cooking Time (mins)']} mins\n"
    response += f"🍽️ **Serving Size:** {filtered_recipe['Serving Size']}\n"
    response += f"🔥 **Calories:** {filtered_recipe['Calories']} kcal\n"
    response += f"💪 **Protein:** {filtered_recipe['Protein (g)']} g\n"
    response += f"🥔 **Carbohydrates:** {filtered_recipe['Carbohydrates (g)']} g\n"
    response += f"🧈 **Fats:** {filtered_recipe['Fats (g)']} g\n"
    response += f"👨‍🍳 **Step-by-Step Cooking Guide:** {filtered_recipe['Step-by-Step Cooking Guide']}\n"

    return response, filtered_recipe['Cooking Instructions']

def ingredient_based_search(ingredients, dietary_preference=None):
    """Find recipes that match the given ingredients."""
    filtered_df = df
    if dietary_preference:
        filtered_df = filtered_df[
            filtered_df["Dietary Preference"].str.contains(dietary_preference, case=False, na=False)]

    matching_recipes = [row["Food Name"] for _, row in filtered_df.iterrows() if
                        all(ing.lower() in row["Ingredients"].lower() for ing in ingredients)]

    return "🍽️ Recipes you can make: " + ", ".join(
        matching_recipes) if matching_recipes else "❌ No recipes found with these ingredients."

def filter_by_diet(dietary_preference):
    """Filter recipes based on dietary preference."""
    filtered_recipes = df[df["Dietary Preference"].str.contains(dietary_preference, case=False, na=False)]
    return "\n🍽️ Recipes for dietary preference: " + ", ".join(filtered_recipes[
                                                                   "Food Name"]) if not filtered_recipes.empty else "❌ No recipes found for this dietary preference."

def speak_recipe_instructions(recipe_details):
    """Speak out the cooking instructions."""
    if recipe_details:
        speak_text(recipe_details)
    else:
        print("❌ No instructions available.")

def add_to_favorites(dish_name):
    """Add a dish to the favorites list if it's not already there."""
    if dish_name not in favorites:
        favorites.append(dish_name)
        print(f"⭐ '{dish_name}' added to favorites!")
    else:
        print(f"✅ '{dish_name}' is already in your favorites!")

def interactive_cooking_guide(dish_name):
    """Step-by-step cooking guide."""
    filtered_recipe = df[df["Food Name"].str.lower() == dish_name.lower()]

    if filtered_recipe.empty:
        return "❌ No instructions available."

    steps = filtered_recipe.iloc[0]["Step-by-Step Cooking Guide"].split(". ")
    for step in steps:
        print(f"➡️ {step}")
        speak_text(step)

    return "✅ Cooking Guide Completed!"

# Route for the home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for the features page
@app.route('/features')
def features():
    return render_template('features.html')

# Global variable to store favorite recipes
favorites = []

# Route to add a recipe to favorites
@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    dish_name = request.form.get('dish_name')
    if dish_name:
        # Check if the dish is already in favorites
        if dish_name not in favorites:
            favorites.append(dish_name)
            print(f"Added to favorites: {dish_name}")
        else:
            print(f"{dish_name} is already in favorites.")
    return redirect(url_for('favourite_recipes'))

# Route to remove a recipe from favorites
@app.route('/remove_from_favorites', methods=['POST'])
def remove_from_favorites():
    dish_name = request.form.get('dish_name')
    if dish_name and dish_name in favorites:
        favorites.remove(dish_name)
        print(f"Removed from favorites: {dish_name}")
    return redirect(url_for('favourite_recipes'))

# Route to display favorite recipes
@app.route('/favourite_recipes')
def favourite_recipes():
    return render_template('favourite_recipes.html', favorites=favorites)

# Route for the blog page
@app.route('/blog')
def blog():
    return render_template('blog.html')

# Route to handle chatbot interactions
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    # Here you can add your chatbot logic to process the user_message
    if user_message.lower() == 'exit':
        return jsonify({'response': 'Goodbye! 👋'})

    # Example chatbot logic
    if "search by dish name" in user_message.lower():
        dish_name = user_message.split("search by dish name")[1].strip()
        recipe_details, _ = get_recipe_details(dish_name)
        return jsonify({'response': recipe_details})
    elif "search by ingredients" in user_message.lower():
        ingredients = user_message.split("search by ingredients")[1].strip().split(",")
        response = ingredient_based_search(ingredients)
        return jsonify({'response': response})
    elif "filter by diet" in user_message.lower():
        diet_preference = user_message.split("filter by diet")[1].strip()
        response = filter_by_diet(diet_preference)
        return jsonify({'response': response})
    elif "speak instructions" in user_message.lower():
        dish_name = user_message.split("speak instructions")[1].strip()
        _, instructions = get_recipe_details(dish_name)
        if instructions:
            speak_text(instructions)
            return jsonify({'response': instructions})
        else:
            return jsonify({'response': "❌ No instructions available."})
    elif "add to favorites" in user_message.lower():
        dish_name = user_message.split("add to favorites")[1].strip()
        add_to_favorites(dish_name)
        return jsonify({'response': f"⭐ '{dish_name}' added to favorites!"})
    elif "interactive guide" in user_message.lower():
        dish_name = user_message.split("interactive guide")[1].strip()
        response = interactive_cooking_guide(dish_name)
        return jsonify({'response': response})
    else:
        return jsonify({'response': "I'm sorry, I didn't understand that. Please try again."})

# Route for Smart Suggestions
@app.route('/smart_suggestions')
def smart_suggestions():
    # Implement logic for smart suggestions
    return render_template('smart_suggestions.html')
# Route to handle recipe search
@app.route('/search_recipe', methods=['POST'])
def search_recipe():
    if request.is_json:
        # Handle JSON-based request
        dish_name = request.json.get('dish_name', '').strip().lower()
    else:
        # Handle form submission
        dish_name = request.form.get('recipe_name', '').strip().lower()

    if not df.empty:
        df['Food Name'] = df['Food Name'].str.strip().str.lower()
        recipe = df[df['Food Name'] == dish_name]

        if not recipe.empty:
            recipe_details = recipe.iloc[0].to_dict()
            if request.is_json:
                return jsonify(recipe_details)
            else:
                return render_template('recipe_details.html', recipes=[recipe_details])
        else:
            if request.is_json:
                return jsonify({'error': 'Recipe not found!'})
            else:
                return render_template('no_recipe_found.html')
    else:
        if request.is_json:
            return jsonify({'error': 'The recipe dataset is not available.'})
        else:
            return render_template('no_recipe_found.html', message="The recipe dataset is not available.")

# Route for voice search
@app.route('/voice_search', methods=['POST'])
def voice_search():
    voice_command = request.json.get('voice_command', '').strip().lower()
    if not df.empty:
        df['Food Name'] = df['Food Name'].str.strip().str.lower()
        recipe = df[df['Food Name'] == voice_command]

        if not recipe.empty:
            recipe_details = recipe.iloc[0].to_dict()
            return jsonify(recipe_details)
        else:
            return jsonify({'error': 'Recipe not found!'})
    else:
        return jsonify({'error': 'The recipe dataset is not available.'})

# Route for Ingredient-Based Search
@app.route('/ingredient_search', methods=['GET', 'POST'])
def ingredient_search():
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        if ingredients:
            ingredients_list = [ing.strip().lower() for ing in ingredients.split(',')]
            matching_recipes = []

            for _, row in df.iterrows():
                recipe_ingredients = row['Ingredients'].lower().split(', ')
                if all(ing in recipe_ingredients for ing in ingredients_list):
                    matching_recipes.append(row.to_dict())

            return render_template('ingredient_search.html', recipes=matching_recipes)
    return render_template('ingredient_search.html')

# API endpoint for ingredient-based search
@app.route('/search_by_ingredients', methods=['POST'])
def search_by_ingredients():
    ingredients = request.form.get('ingredients')
    if ingredients:
        ingredients_list = [ing.strip().lower() for ing in ingredients.split(',')]
        matching_recipes = []

        for _, row in df.iterrows():
            recipe_ingredients = row['Ingredients'].lower().split(', ')
            if all(ing in recipe_ingredients for ing in ingredients_list):
                matching_recipes.append(row.to_dict())

        return jsonify(matching_recipes)
    return jsonify({'error': 'No ingredients provided.'})

# Route for Quick Recipes
@app.route('/quick_recipes', methods=['GET', 'POST'])
def quick_recipes():
    if request.method == 'POST':
        cooking_time = request.form.get('cooking_time')
        if cooking_time:
            try:
                cooking_time = int(cooking_time)
                # Define the time range (e.g., 15-20 for input 20, 20-25 for input 25, etc.)
                lower_bound = cooking_time - 5
                upper_bound = cooking_time

                # Filter recipes within the time range
                matching_recipes = df[
                    (df['Cooking Time (mins)'] >= lower_bound) &
                    (df['Cooking Time (mins)'] <= upper_bound)
                ]

                # Group recipes by cooking time
                grouped_recipes = {}
                for _, row in matching_recipes.iterrows():
                    time = row['Cooking Time (mins)']
                    if time not in grouped_recipes:
                        grouped_recipes[time] = []
                    grouped_recipes[time].append(row.to_dict())

                return render_template('quick_recipes.html', grouped_recipes=grouped_recipes)
            except ValueError:
                return render_template('quick_recipes.html', error="Invalid cooking time. Please enter a number.")
        else:
            return render_template('quick_recipes.html', error="Please enter a cooking time.")
    return render_template('quick_recipes.html')

# API endpoint for quick recipes
@app.route('/search_quick_recipes', methods=['POST'])
def search_quick_recipes():
    cooking_time = request.form.get('cooking_time')
    if cooking_time:
        try:
            cooking_time = int(cooking_time)
            # Define the time range (e.g., 15-20 for input 20, 20-25 for input 25, etc.)
            lower_bound = cooking_time - 5
            upper_bound = cooking_time

            # Filter recipes within the time range
            matching_recipes = df[
                (df['Cooking Time (mins)'] >= lower_bound) &
                (df['Cooking Time (mins)'] <= upper_bound)
            ]

            # Group recipes by cooking time
            grouped_recipes = {}
            for _, row in matching_recipes.iterrows():
                time = row['Cooking Time (mins)']
                if time not in grouped_recipes:
                    grouped_recipes[time] = []
                grouped_recipes[time].append(row.to_dict())

            return jsonify(grouped_recipes)
        except ValueError:
            return jsonify({'error': 'Invalid cooking time. Please enter a number.'})
    return jsonify({'error': 'Please enter a cooking time.'})

# Route for the meal planner page
@app.route('/meal_planner')
def meal_planner():
    return render_template('meal_planner.html')

@app.route('/generate_meal_plan', methods=['POST'])
def generate_meal_plan():
    preferences = request.json.get('preferences', [])
    if not preferences:
        return jsonify({'error': 'Please select at least one dietary preference.'})

    # Debug: Print selected preferences
    print("Selected Preferences:", preferences)

    # Filter recipes based on dietary preferences
    filtered_df = df[df['Dietary Preference'].apply(lambda x: any(pref in x for pref in preferences))]

    # Debug: Print filtered dataset
    print("Filtered Dataset:", filtered_df)

    if filtered_df.empty:
        return jsonify({'error': 'No recipes found for the selected preferences.'})

    # Randomly select meals for morning, afternoon, and night
    try:
        morning_meal = filtered_df.sample(1)['Food Name'].iloc[0]
        afternoon_meal = filtered_df.sample(1)['Food Name'].iloc[0]
        night_meal = filtered_df.sample(1)['Food Name'].iloc[0]
    except IndexError:
        return jsonify({'error': 'Not enough recipes to generate a meal plan.'})

    # Debug: Print selected meals
    print("Morning Meal:", morning_meal)
    print("Afternoon Meal:", afternoon_meal)
    print("Night Meal:", night_meal)

    return jsonify({
        'morning': morning_meal,
        'afternoon': afternoon_meal,
        'night': night_meal,
    })

# Route for Dietary Filter
@app.route('/dietary_filter', methods=['GET', 'POST'])
def dietary_filter():
    if request.method == 'POST':
        diet = request.form.get('diet').lower()
        if diet:
            # Filter recipes based on dietary preference using the DataFrame (df)
            filtered_recipes = df[df['Dietary Preference'].str.lower() == diet]
            # Convert the filtered DataFrame to a list of dictionaries
            filtered_recipes_list = filtered_recipes.to_dict(orient='records')
            return render_template('dietary_filter.html', filtered_recipes=filtered_recipes_list)
        else:
            return render_template('dietary_filter.html', error="Please enter a dietary preference.")
    return render_template('dietary_filter.html')

# API endpoint for dietary filter
@app.route('/filter_by_diet', methods=['POST'])
def filter_by_diet():
    diet = request.form.get('diet').lower()

    # Filter recipes based on dietary preference using the DataFrame (df)
    filtered_recipes = df[df['Dietary Preference'].str.lower() == diet]
    # Convert the filtered DataFrame to a list of dictionaries
    filtered_recipes_list = filtered_recipes.to_dict(orient='records')
    return jsonify(filtered_recipes_list if not filtered_recipes.empty else [])

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)