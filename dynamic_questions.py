import openai
import json
from config import API_KEY

openai.api_key = API_KEY

def generate_questions(recipe_name, ingredients):
    """Generate recipe-specific questions using AI."""
    try:
        ingredients_list = ', '.join(ingredients)
        prompt = f"""Generate questions about cooking {recipe_name} with these ingredients: {ingredients_list}

You must respond with ONLY a JSON array of questions. Each question object must have these exact fields:
- "text": string with the question text
- "type": string that is either "choice" or "text"
- "options": array of strings (REQUIRED only when type is "choice")

REQUIRED INFORMATION TO GATHER (ask only what applies to the recipe):
1. CRITICAL MEASUREMENTS that affect cooking time/temperature:
   - For steaks: Thickness (e.g., 1 inch, 1.5 inches)
   - For roasts: Weight and thickness
   - For whole poultry: Weight
   - For baked goods: Pan size and thickness
   These measurements are REQUIRED when they affect cooking time/temperature

2. Cooking method preference (e.g., deep frying, baking, air frying)

3. Desired outcome:
   - For meats: Doneness level (except chicken)
   - For all: Texture preferences (e.g., crispiness)
   - Heat level when relevant (e.g., spiciness)

4. Essential equipment ONLY AFTER cooking method is chosen:
   - If baking: Ask about oven type and pan size
   - If grilling: Ask about grill type
   - If deep frying: Ask about thermometer availability
   DO NOT ask method-specific questions before knowing the method!

RECIPE-SPECIFIC RULES:
For Steak:
- ALWAYS ask about thickness first (critical for achieving desired doneness)
- Include doneness levels (rare to well done)
- Ask about meat thermometer availability
- Focus on cooking method

For Chicken:
- DO NOT ask about doneness (must be fully cooked)
- Focus on texture and crispiness
- Ask about heat/spice level if relevant
- DO NOT ask about equipment until cooking method is chosen

For Baked Goods:
- Ask about pan size/dimensions
- Ask about oven type
- Focus on texture preferences

Format Guidelines:
- Each question must have 3-5 PRECISE options
- Include measurements in both imperial and metric
- Always include "Other" as the last option for choice questions
- Make questions specific to the recipe type

Example valid response for chicken wings:
[
    {{
        "text": "What is your desired texture for the chicken wings?",
        "type": "choice",
        "options": ["Extra Crispy", "Crispy outside, juicy inside", "Tender and juicy", "Other"]
    }},
    {{
        "text": "What is your preferred cooking method for the chicken wings?",
        "type": "choice",
        "options": ["Deep fried", "Baked", "Air fried", "Grilled", "Other"]
    }}
]

IMPORTANT RULES:
1. ALWAYS ask about physical measurements when they affect cooking time/temperature
2. Questions MUST help achieve the exact desired outcome
3. Questions MUST be relevant to cooking technique and timing
4. DO NOT ask about:
   - Seasoning preferences (except spice level when relevant)
   - Plating or serving suggestions
   - Nutritional information
   - Ingredient substitutions
   - Preparation steps
   - Equipment implied by cooking method
5. Keep questions concise and clear
6. Only ask questions that are necessary for this specific recipe type
7. NEVER ask equipment-specific questions before knowing the cooking method
8. Equipment and method-specific questions should be handled by the application AFTER the cooking method is selected"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert chef creating a customized recipe questionnaire. Your goal is to ask only the most essential questions that will help create precise and helpful cooking instructions.

FOCUS ON:
1. CRITICAL MEASUREMENTS:
   - Physical measurements that affect cooking time/temperature
   - These are REQUIRED for precise cooking instructions
   - Examples: steak thickness, roast weight

2. COOKING METHOD AND OUTCOME:
   - Preferred cooking method
   - Desired texture/doneness
   - Heat/spice preferences when relevant

3. ESSENTIAL EQUIPMENT:
   - ONLY ask after cooking method is chosen
   - NEVER assume a cooking method
   - Equipment questions should be handled after method selection

4. RECIPE-SPECIFIC CONSIDERATIONS:
   - For steak: ALWAYS ask thickness, doneness, and thermometer availability
   - For chicken: Focus on texture (never ask about doneness)
   - For baked goods: Ask pan size and oven type ONLY if baking is chosen

DO NOT ASK ABOUT:
- Equipment before knowing cooking method
- Equipment implied by cooking method
- Doneness levels for chicken
- Seasoning preferences (except spice level when relevant)
- Plating or presentation
- Preparation steps
- Specific cooking times

EXAMPLES OF GOOD QUESTIONS:
✅ "How thick is your steak?" (with precise measurements)
✅ "What is your preferred cooking method?"
✅ "What level of doneness would you like?"
✅ "How crispy would you like your wings?"

EXAMPLES OF BAD QUESTIONS:
❌ "What type of oven do you have?" (before knowing if baking)
❌ "What size pan will you use?" (before knowing cooking method)
❌ "Do you have a grill?" (when method not yet chosen)
❌ "How well done would you like your chicken?"

Each question must directly impact the cooking instructions and help achieve the exact desired outcome. NEVER assume a cooking method when asking questions."""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # Get the response content and clean it
        content = response.choices[0].message['content'].strip()
        
        # Remove any potential markdown code block markers and extra whitespace
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Handle potential leading/trailing brackets or whitespace
        content = content.strip('`').strip()
        if not content.startswith('['):
            # Try to find the start of the JSON array
            start_idx = content.find('[')
            if start_idx != -1:
                content = content[start_idx:]
            else:
                return {
                    "status": "error",
                    "message": "Invalid response format. Expected a JSON array.",
                    "questions": []
                }
        
        print("Raw AI response:", content)  # Debug log
        
        try:
            questions = json.loads(content)
            
            # Validate the structure
            if not isinstance(questions, list):
                return {
                    "status": "error",
                    "message": "Invalid response format. Expected a JSON array.",
                    "questions": []
                }
            
            # Validate each question
            validated_questions = []
            for q in questions:
                if not isinstance(q, dict):
                    continue
                    
                if 'text' not in q or 'type' not in q:
                    continue
                    
                if not isinstance(q['text'], str) or not isinstance(q['type'], str):
                    continue
                    
                if q['type'] not in ['choice', 'text']:
                    q['type'] = 'text'  # Default to text if invalid type
                    
                if q['type'] == 'choice':
                    if 'options' not in q or not isinstance(q['options'], list):
                        continue
                    if not all(isinstance(opt, str) for opt in q['options']):
                        continue
                        
                validated_questions.append(q)
            
            if not validated_questions:
                return {
                    "status": "error",
                    "message": "No valid questions were found in the response.",
                    "questions": []
                }
                
            return {
                "status": "success",
                "questions": validated_questions
            }
            
        except json.JSONDecodeError as e:
            print("JSON parsing error:", str(e))  # Debug log
            print("Invalid JSON content:", content)  # Debug log
            return {
                "status": "error",
                "message": "Failed to parse the generated questions. Please try again.",
                "questions": []
            }
            
    except Exception as e:
        print("Error in generate_questions:", str(e))  # Debug log
        return {
            "status": "error",
            "message": "An unexpected error occurred. Please try again.",
            "questions": []
        } 