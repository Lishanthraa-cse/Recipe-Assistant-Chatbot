import speech_recognition as sr
from fuzzywuzzy import process
import pyttsx3
import pandas as pd

# Load dataset
df = pd.read_csv("datasets/All_Recipes_Cleaned.csv", encoding="ISO-8859-1")

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()


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


# Main Chatbot Loop
favorites = []
print("🤖 Welcome to the AI-Powered Recipe Assistant! Type 'exit' to stop.")
while True:
    print("\n🔹 Choose an Option:")
    print("1️⃣ Search by Dish Name")
    print("2️⃣ Search by Ingredients")
    print("3️⃣ Filter by Dietary Preference")
    print("4️⃣ Speak the Cooking Instructions")
    print("5️⃣ Show Favorite Recipes")
    print("6️⃣ Step-by-Step Interactive Cooking Guide")
    print("7️⃣ Exit")

    choice = input("Enter your choice (1-7): ").strip()

    if choice == "1":
        print("\n🔹 Choose Input Mode:")
        print("1️⃣ Speak the dish name 🎙️")
        print("2️⃣ Type the dish name ⌨️")
        mode = input("Enter your choice (1/2): ").strip()
        user_input = recognize_speech() if mode == "1" else input("\nWhich dish would you like details for? ").strip()
        if user_input.lower() == "exit":
            break
        recipe_details, _ = get_recipe_details(user_input)
        print(recipe_details)

    elif choice == "2":
        user_ingredients = input("\nEnter available ingredients (comma-separated): ").strip()
        if user_ingredients.lower() == "exit":
            break
        print(ingredient_based_search(user_ingredients.split(",")))

    elif choice == "3":
        diet_preference = input("\nEnter dietary preference(Vegetarian, Vegan, High-Protein, Gluten-Free, Low-Calorie, Non-Vegetarian, Keto-Friendly, Probiotic, High-Calorie): ").strip()
        if diet_preference.lower() == "exit":
            break
        print(filter_by_diet(diet_preference))

    elif choice == "4":
        dish_name = input("\nEnter the dish name to read its instructions: ").strip()
        if dish_name.lower() == "exit":
            break
        _, instructions = get_recipe_details(dish_name)
        if instructions:
            print(instructions)
            speak_text(instructions)
        else:
            print("❌ No instructions available.")

    elif choice == "5":
        if not favorites:
            print("⭐ No favorite recipes saved yet!")
        else:
            print("\n⭐ Favorite Recipes:")
            for idx, recipe in enumerate(favorites, start=1):
                print(f"{idx}. {recipe}")
        add_fav = input("\nWould you like to add a dish to favorites? (yes/no): ").strip().lower()
        if add_fav == "yes":
            fav_dish = input("Enter the dish name to add: ").strip()
            add_to_favorites(fav_dish)
        elif add_fav != "no":
            print("⚠️ Invalid choice! Please enter 'yes' or 'no'.")

    elif choice == "6":
        dish_name = input("\nEnter the dish name for step-by-step guidance: ").strip()
        if dish_name.lower() == "exit":
            break
        print(interactive_cooking_guide(dish_name))

    elif choice == "7":
        print("Goodbye! 👋")
        break
    else:
        print("⚠️ Invalid choice! Please enter a number from 1 to 7.")
