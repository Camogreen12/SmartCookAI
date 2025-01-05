from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path
import openai
from config import API_KEY, SECRET_KEY, DEBUG
from ingredient_suggestions import generate_ingredients
from dynamic_questions import generate_questions
from instructions_generator import generate_instructions, answer_question
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/static/*": {"origins": "*"},
    r"/api/*": {"origins": "*"}
})

app.config['SECRET_KEY'] = SECRET_KEY
openai.api_key = API_KEY

# Ensure required directories exist
Path("data").mkdir(exist_ok=True)
Path("ai_prompts").mkdir(exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recipe_input')
def recipe_input():
    return render_template('recipe_input.html')

@app.route('/ingredients')
def ingredients():
    return render_template('ingredients.html')

@app.route('/questions')
def questions():
    return render_template('questions.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/api/generate_ingredients', methods=['POST'])
def generate_ingredients_route():
    recipe_name = request.json.get('recipe_name')
    if not recipe_name:
        return jsonify({'status': 'error', 'message': 'Recipe name is required'})
    
    # Get the quantity from the request
    quantity = request.json.get('quantity')
    if quantity and str(quantity).isdigit():
        # If quantity is provided, ensure it's prepended to the recipe name
        recipe_parts = recipe_name.split()
        if recipe_parts[0].isdigit():
            # If recipe name already has a quantity, replace it
            recipe_name = f"{quantity} {' '.join(recipe_parts[1:])}"
        else:
            # If no quantity in recipe name, add it
            recipe_name = f"{quantity} {recipe_name}"
    
    result = generate_ingredients(recipe_name)
    return jsonify(result)

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions_route():
    try:
        recipe_name = request.json.get('recipe_name')
        ingredients = request.json.get('ingredients', [])
        
        if not recipe_name:
            return jsonify({
                'status': 'error',
                'message': 'Recipe name is required',
                'questions': []
            }), 400
        
        if not ingredients:
            return jsonify({
                'status': 'error',
                'message': 'No ingredients provided',
                'questions': []
            }), 400
        
        print("Generating questions for recipe:", recipe_name)  # Debug log
        print("With ingredients:", ingredients)  # Debug log
        
        result = generate_questions(recipe_name, ingredients)
        print("AI Response:", result)  # Debug log
        
        if result.get('status') == 'error':
            return jsonify(result), 400
            
        if not result.get('questions'):
            return jsonify({
                'status': 'error',
                'message': 'No questions were generated. Please try again.',
                'questions': []
            }), 400
            
        return jsonify(result)
        
    except Exception as e:
        print("Error in generate_questions_route:", str(e))  # Debug log
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.',
            'questions': []
        }), 500

@app.route('/api/generate_instructions', methods=['POST'])
def generate_instructions_route():
    recipe_name = request.json.get('recipe_name')
    ingredients = request.json.get('ingredients', [])
    answers = request.json.get('answers', [])
    
    if not recipe_name:
        return jsonify({'status': 'error', 'message': 'Recipe name is required'})
    
    result = generate_instructions(recipe_name, ingredients, answers)
    return jsonify(result)

@app.route('/api/ask_question', methods=['POST'])
def ask_question_route():
    question = request.json.get('question')
    recipe_name = request.json.get('recipe_name')
    current_step = request.json.get('current_step', 0)
    instructions = request.json.get('instructions', [])
    
    if not all([question, recipe_name]):
        return jsonify({'status': 'error', 'message': 'Question and recipe name are required'})
    
    result = answer_question(question, recipe_name, current_step, instructions)
    return jsonify(result)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,xi-api-key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=DEBUG) 