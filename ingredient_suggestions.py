import openai
from config import API_KEY

openai.api_key = API_KEY

def load_prompt():
    """Load the ingredient suggestion prompt template."""
    return """Given a recipe for {recipe}, suggest a comprehensive list of ingredients with quantities.
    Format each ingredient on a new line with ONLY the quantity and unit of measurement followed by the ingredient name.
    DO NOT add any numbering or prefixes to the lines.
    DO NOT include substitutions or optional ingredients.
    If a specific quantity of the main item is provided (e.g., '5 steak'), make sure to adjust ALL ingredients accordingly.
    Examples of correct format:
    2 tablespoons olive oil
    4 cloves garlic, minced
    1/2 teaspoon salt
    """

def generate_ingredients(recipe_name):
    """Generate a list of ingredients for the given recipe using AI."""
    try:
        # Parse quantity from recipe name if present
        parts = recipe_name.split()
        quantity = 1
        base_recipe = recipe_name
        
        if len(parts) > 1 and parts[0].isdigit():
            quantity = int(parts[0])
            base_recipe = ' '.join(parts[1:])
        
        prompt = f"""Given a recipe for {quantity} {base_recipe}, suggest a comprehensive list of ingredients with quantities.
        Format each ingredient on a new line with ONLY the quantity and unit of measurement followed by the ingredient name.
        DO NOT add any numbering or prefixes to the lines.
        DO NOT include substitutions or optional ingredients.
        IMPORTANT: This recipe is for {quantity} {base_recipe}, so adjust ALL ingredient quantities accordingly.
        
        Examples of correct format:
        For 1 steak:
        2 tablespoons olive oil
        2 cloves garlic, minced
        1/2 teaspoon salt
        
        For {quantity} {base_recipe}:
        {quantity} {base_recipe}
        (adjust other quantities accordingly)"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a professional chef helping to create detailed ingredient lists. This recipe is specifically for {quantity} {base_recipe}, so ensure all quantities are adjusted accordingly. Always list the main ingredient first with the exact quantity specified."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse the response into a list of ingredients
        ingredients_text = response.choices[0].message.content.strip()
        ingredients = [line.strip() for line in ingredients_text.split('\n') if line.strip()]
        
        # Ensure the main ingredient quantity matches the requested quantity
        if base_recipe.lower() in ['steak', 'chicken', 'fish']:
            main_ingredient = f"{quantity} {base_recipe}"
            # Remove any existing main ingredient entries and add the correct one at the start
            ingredients = [main_ingredient] + [ing for ing in ingredients if base_recipe.lower() not in ing.lower()]
        
        return {
            "status": "success",
            "ingredients": ingredients
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "ingredients": []
        } 