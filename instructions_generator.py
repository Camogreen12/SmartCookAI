import openai
from config import API_KEY
import re, json

openai.api_key = API_KEY

def load_prompt():
    """Load the instruction generation prompt template."""
    return """Create detailed cooking instructions for {recipe} with the following details:

Ingredients:
{ingredients}

User Preferences:
{preferences}

Generate step-by-step instructions that are clear, precise, and easy to follow.
Include cooking times, temperatures, and visual cues for doneness.
Format each step on a new line, numbered from 1.
Include safety warnings and tips where appropriate."""

def format_preferences(answers):
    """Format the user's answers into a readable preferences string."""
    if not answers:
        return "No preferences specified"
    
    formatted_answers = []
    for answer in answers:
        if isinstance(answer, dict) and 'question' in answer and 'answer' in answer:
            formatted_answers.append(f"- {answer['question']}: {answer['answer']}")
        elif isinstance(answer, str):
            formatted_answers.append(f"- Preference: {answer}")
    
    return "\n".join(formatted_answers) if formatted_answers else "No preferences specified"

def generate_instructions(recipe_name, ingredients, answers):
    """Generate detailed cooking instructions using AI."""
    try:
        print(f"Generating instructions for recipe: {recipe_name}")  # Debug log
        print(f"Ingredients: {ingredients}")  # Debug log
        print(f"Answers: {answers}")  # Debug log
        
        ingredients_text = "\n".join(f"- {ingredient}" for ingredient in ingredients)
        preferences_text = format_preferences(answers)
        
        messages = [
            {
                "role": "system",
                "content": """You are a professional Michelin-starred chef creating detailed cooking instructions. 
Your instructions MUST follow these STRICT rules:

1. NEVER use short headers or titles. Each step must be a complete, detailed instruction.
   BAD: "**Prepare Wet Ingredients:**"
   GOOD: "In a large mixing bowl, combine 2 room-temperature eggs, 1 cup of milk (heated to 110°F), and 1 teaspoon of vanilla extract. Whisk thoroughly until well combined and slightly frothy, about 30 seconds."

2. Each step MUST include:
   - Exact measurements and quantities
   - Precise timing (in minutes/seconds)
   - Specific temperatures where applicable
   - Clear visual or sensory indicators
   - Equipment specifications (size of bowl, type of whisk, etc.)

3. Format each step as a complete paragraph with all details included.
   - No bullet points
   - No section headers
   - Just numbered, detailed steps

4. ALWAYS start with preparation steps:
   - Exact preheating temperatures
   - Equipment preparation
   - Ingredient preparation (e.g., bringing to room temperature)

5. Include safety warnings and tips within the relevant steps.

6. For steaks and similar meats, ALWAYS separate the cooking into two distinct phases:
   Phase 1 - Initial Searing:
   - First sear each side WITHOUT moving (3-4 minutes per side) to develop a crust
   - Specify "without moving" during the searing phase
   - Make this a separate, dedicated step

   Phase 2 - Finishing/Internal Cooking:
   - AFTER initial searing, start frequent flipping (every 30-45 seconds)
   - Make this a separate, dedicated step
   - Specify that this is to achieve desired internal temperature
   - Include total expected time for this phase

7. For ANY other step that involves additional cooking time:
   - Specify if the food should be flipped/turned/rotated
   - Include which side to cook on
   - Specify total cooking time per side
   - For doneness checks, specify which side to cook on

8. Use this format for each step:
   1. [Complete, detailed instruction including all measurements, times, temperatures, and specific cooking method]
   2. [Next complete, detailed instruction]
   (etc.)

Remember: Each step should be able to stand alone as a complete instruction with no additional context needed."""
            },
            {
                "role": "user",
                "content": f"""Create detailed cooking instructions for this recipe:

Recipe Name: {recipe_name}

Ingredients:
{ingredients_text}

User Preferences:
{preferences_text}

Remember to make each step a complete, detailed instruction - no headers or short titles."""
            }
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,  # Lowered from 1.0 to 0.7 for more consistent formatting
            max_tokens=3000
        )
        
        # Parse the response into a list of instructions
        instructions_text = response.choices[0].message.content.strip()
        print(f"Raw AI response: {instructions_text}")  # Debug log
        
        # Clean up the response text
        instructions_text = instructions_text.replace('```json', '').replace('```', '').strip()
        if not instructions_text.startswith('{'):
            start_idx = instructions_text.find('{')
            if start_idx != -1:
                instructions_text = instructions_text[start_idx:]
            end_idx = instructions_text.rfind('}')
            if end_idx != -1:
                instructions_text = instructions_text[:end_idx + 1]
        
        try:
            # Try to parse the JSON response
            instructions_data = json.loads(instructions_text)
            print(f"Parsed JSON data: {json.dumps(instructions_data, indent=2)}")  # Debug log
            
            # Validate the response structure
            if not isinstance(instructions_data, dict):
                raise ValueError("Invalid response format: root must be an object")
            
            if "steps" not in instructions_data:
                # Try to find steps at the root level
                if all(isinstance(step, dict) for step in instructions_data.values()):
                    instructions_data = {"steps": list(instructions_data.values())}
                else:
                    raise ValueError("Invalid response format: missing 'steps' array")
            
            if not isinstance(instructions_data["steps"], list):
                raise ValueError("Invalid response format: 'steps' is not an array")
            
            # Validate each step has required fields
            validated_steps = []
            for step in instructions_data["steps"]:
                if not isinstance(step, dict):
                    print(f"Skipping invalid step: {step}")
                    continue
                
                action = str(step.get("action", "")).strip()
                if not action:
                    print(f"Skipping step with empty action: {step}")
                    continue
                
                # Check if user’s action says “on each side” or “both sides”
                if ("on each side" in action.lower() or "both sides" in action.lower()) and "cook for" in action.lower():
                    # Attempt to extract the time from text like "Cook for about 6-8 minutes on each side"
                    time_match = re.search(r'[Cc]ook\s+for\s+about\s+(\d+(-\d+)?)\s*[–-]?\s*(\d+)?\s*minutes', action)
                    # The above regex tries to capture "6-8" or single "6" or "6 - 8"

                    if time_match:
                        # e.g. match might be "6-8"
                        minute_range = time_match.group(1)  # "6-8" or "6"
                        # Create step 1: Cook on first side
                        first_side_action = (f"Place the chicken drumsticks in the pan, skin side down, and "
                                             f"cook for about {minute_range} minutes on the first side, or until lightly browned.")

                        validated_steps.append({
                            "action": first_side_action,
                            "timing": step.get("timing", {}),
                            "technique": step.get("technique", {}),
                            "safety": step.get("safety", {}),
                            "sensory_cues": step.get("sensory_cues", {}),
                            "why": str(step.get("why", "")).strip(),
                            "note": str(step.get("note", "")).strip(),
                            "temperature": step.get("temperature", {}),
                            "equipment": step.get("equipment", {}),
                            "measurements": step.get("measurements", {}),
                            "warnings": step.get("warnings", [])
                        })

                        # Create step 2: Flip and cook second side
                        second_side_action = (f"Flip the chicken drumsticks and cook for another {minute_range} minutes on the second side, "
                                              f"or until the internal temperature reaches 165°F (74°C).")
                        
                        validated_steps.append({
                            "action": second_side_action,
                            "timing": step.get("timing", {}),
                            "technique": step.get("technique", {}),
                            "safety": step.get("safety", {}),
                            "sensory_cues": step.get("sensory_cues", {}),
                            "why": str(step.get("why", "")).strip(),
                            "note": str(step.get("note", "")).strip(),
                            "temperature": step.get("temperature", {}),
                            "equipment": step.get("equipment", {}),
                            "measurements": step.get("measurements", {}),
                            "warnings": step.get("warnings", [])
                        })
                    else:
                        # If we cannot parse the minutes, still split into two steps
                        validated_steps.append({
                            "action": "Place chicken on the first side and cook until browned.",
                            "timing": step.get("timing", {}),
                            "technique": step.get("technique", {}),
                            "safety": step.get("safety", {}),
                            "sensory_cues": step.get("sensory_cues", {}),
                            "why": str(step.get("why", "")).strip(),
                            "note": str(step.get("note", "")).strip(),
                            "temperature": step.get("temperature", {}),
                            "equipment": step.get("equipment", {}),
                            "measurements": step.get("measurements", {}),
                            "warnings": step.get("warnings", [])
                        })
                        validated_steps.append({
                            "action": "Flip the chicken to the other side and cook until the internal temperature reaches 165°F (74°C).",
                            "timing": step.get("timing", {}),
                            "technique": step.get("technique", {}),
                            "safety": step.get("safety", {}),
                            "sensory_cues": step.get("sensory_cues", {}),
                            "why": str(step.get("why", "")).strip(),
                            "note": str(step.get("note", "")).strip(),
                            "temperature": step.get("temperature", {}),
                            "equipment": step.get("equipment", {}),
                            "measurements": step.get("measurements", {}),
                            "warnings": step.get("warnings", [])
                        })
                else:
                    # Not mentioning "each side" or "both sides", keep it as is
                    validated_steps.append({
                        "action": action,
                        "timing": step.get("timing", {}),
                        "technique": step.get("technique", {}),
                        "safety": step.get("safety", {}),
                        "sensory_cues": step.get("sensory_cues", {}),
                        "why": str(step.get("why", "")).strip(),
                        "note": str(step.get("note", "")).strip(),
                        "temperature": step.get("temperature", {}),
                        "equipment": step.get("equipment", {}),
                        "measurements": step.get("measurements", {}),
                        "warnings": step.get("warnings", [])
                    })
            
            if not validated_steps:
                raise ValueError("No valid steps found in response")
            
            # Return the validated steps
            result = {
                "status": "success",
                "instructions": validated_steps
            }
            print(f"Returning result: {json.dumps(result, indent=2)}")  # Debug log
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing response: {str(e)}")  # Debug log
            print(f"Failed to parse: {instructions_text}")  # Debug log
            
            # Fallback: If JSON parsing fails, extract steps the old way
            instructions = []
            for line in instructions_text.split('\n'):
                line = line.strip()
                if not line or line.lower().startswith('ingredients:'):
                    continue
                    
                if line[0].isdigit() and '. ' in line:
                    instruction = line.split('. ', 1)[1].strip()
                    if instruction:
                        instructions.append({
                            "action": instruction,
                            "why": "",
                            "note": ""
                        })
            
            if not instructions:
                return {
                    "status": "error",
                    "message": "Failed to generate instructions",
                    "instructions": []
                }
            
            result = {
                "status": "success",
                "instructions": instructions
            }
            print(f"Returning fallback result: {json.dumps(result, indent=2)}")  # Debug log
            return result
        
    except Exception as e:
        print(f"Error generating instructions: {str(e)}")  # Debug log
        return {
            "status": "error",
            "message": str(e),
            "instructions": []
        }

def answer_question(question, recipe_name, current_step, instructions, conversation_context=None):
    """Answer a user's question about a specific step or the recipe in general."""
    try:
        # Get the full recipe context
        all_steps = "\n".join([f"Step {i+1}: {step['action']}" for i, step in enumerate(instructions)])
        
        # Special handling for timing questions with context
        is_timing_question = conversation_context and conversation_context.get('is_timing_question', False)
        
        # If we have conversation context and are discussing a specific step
        if (conversation_context and current_step >= 0) or is_timing_question:
            # Get the current step being discussed
            current_step_info = instructions[current_step]
            
            # Get surrounding steps for context
            prev_step = instructions[current_step - 1]['action'] if current_step > 0 else None
            next_step = instructions[current_step + 1]['action'] if current_step < len(instructions) - 1 else None
            
            # Build detailed context about the current conversation
            if is_timing_question:
                step_context = f"""Current conversation context:
We are specifically discussing timing for step {current_step + 1} of the recipe:
{current_step_info['action']}

The user is asking about timing or duration for this specific step.
Please provide a clear answer about timing that is specific to this step and considers any modifications mentioned in the question.

Previous step {current_step}: {prev_step if prev_step else "No previous step"}
Next step {current_step + 2}: {next_step if next_step else "No next step"}"""
            else:
                step_context = f"""Current conversation context:
We are actively discussing step {current_step + 1} of the recipe:
{current_step_info['action']}

Last discussed topic: {conversation_context.get('last_topic', 'None')}
Last action performed: {conversation_context.get('last_action', 'None')}

Previous step {current_step}: {prev_step if prev_step else "No previous step"}
Next step {current_step + 2}: {next_step if next_step else "No next step"}

The user's question appears to be specifically about the current step and its actions."""
        else:
            step_context = "This is a general question about the recipe. Here are all the steps:\n" + all_steps

        context = f"""Recipe: {recipe_name}

Full Recipe Context:
{all_steps}

Specific Context:
{step_context}

Question: {question}

Provide a clear, direct answer that:
1. Is specifically focused on the current step being discussed (if the question is step-specific)
2. Maintains context of what the user is currently doing
3. Is professional and accurate
4. Is easy to understand
5. Contains no unnecessary explanations
6. Uses no fluff or filler words
7. Gives just the essential information needed
8. For timing questions, provides specific durations and considers any modifications mentioned"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional chef giving quick, clear answers. 
- Be direct and concise
- Use simple language
- Skip unnecessary context
- Focus only on what was asked
- No pleasantries or extra explanations
- Just give the essential information
- Make sure your answer matches the current recipe and step exactly
- If discussing a specific step, keep your answer relevant to that step's context
- For timing questions, be specific about durations and consider any modifications mentioned"""
                },
                {"role": "user", "content": context}
            ],
            temperature=0.5,  # Lower temperature for more focused responses
            max_tokens=200    # Reduced max tokens to encourage brevity
        )
        
        return {
            "status": "success",
            "answer": response.choices[0].message.content.strip()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "answer": "Sorry, I couldn't process your question. Please try again."
        } 