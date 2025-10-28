from flask import Blueprint, jsonify, request
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

translate_bp = Blueprint('translate', __name__)

def get_openai_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    return OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )

@translate_bp.route('/generate', methods=['POST'])
def generate_note():
    """Generate note from natural language description"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        description = data.get('description', '')
        output_language = data.get('output_language', 'English')
        current_date = data.get('current_date', '')
        current_datetime = data.get('current_datetime', '')
        
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        
        system_prompt = f'''Extract the user's notes into the following structured fields:
1. Title: A concise title of the notes less than 5 words
2. Notes: The notes based on user input written in full sentences.
3. Tags (A list): At most 3 Keywords or tags that categorize the content of the notes.
4. EventDate: If the description mentions a date (like "tomorrow", "next Monday", specific date), extract it in YYYY-MM-DD format. Leave null if no date mentioned.
5. EventTime: If the description mentions a time (like "5pm", "14:00"), extract it in HH:MM 24-hour format. Leave null if no time mentioned.

IMPORTANT: Current date and time context:
- Today is: {current_date}
- Current datetime: {current_datetime}
- Use this information to calculate relative dates like "tomorrow", "next week", "next Monday", etc.

Output in JSON format without ```json. Output title and notes in the language: {output_language}.

Example 1:
Input: "Badminton tmr 5pm @polyu" (assuming today is Monday, January 15, 2024)
Output:
{{
"Title": "Badminton at PolyU", 
"Notes": "Remember to play badminton at 5pm tomorrow at PolyU.",
"Tags": ["badminton", "sports"],
"EventDate": "2024-01-16",
"EventTime": "17:00"
}}

Example 2:
Input: "Team meeting next Monday at 2pm to discuss Q4 goals" (assuming today is Wednesday, January 10, 2024)
Output:
{{
"Title": "Q4 Team Meeting",
"Notes": "Team meeting scheduled for next Monday at 2pm to discuss Q4 goals.",
"Tags": ["meeting", "Q4", "team"],
"EventDate": "2024-01-15",
"EventTime": "14:00"
}}

Example 3:
Input: "Remember to buy groceries"
Output:
{{
"Title": "Buy Groceries",
"Notes": "Remember to buy groceries.",
"Tags": ["shopping", "groceries"],
"EventDate": null,
"EventTime": null
}}
'''
        
        client = get_openai_client()
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": description,
                }
            ],
            temperature=0.7,
            model="gpt-4o-mini",
        )
        
        # Parse the response
        import json
        generated_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if generated_text.startswith('```'):
            lines = generated_text.split('\n')
            generated_text = '\n'.join(lines[1:-1])
        
        generated_data = json.loads(generated_text)
        
        # Format tags as comma-separated string
        tags_list = generated_data.get('Tags', [])
        tags_string = ', '.join(tags_list) if isinstance(tags_list, list) else str(tags_list)
        
        return jsonify({
            'title': generated_data.get('Title', ''),
            'content': generated_data.get('Notes', ''),
            'tags': tags_string,
            'event_date': generated_data.get('EventDate'),
            'event_time': generated_data.get('EventTime')
        })
        
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

@translate_bp.route('/translate', methods=['POST'])
def translate_note():
    """Translate note title, content, and tags to target language"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', '')
        target_language = data.get('target_language', 'English')
        
        if not title and not content and not tags:
            return jsonify({'error': 'Nothing to translate'}), 400
        
        # Create prompt for translation
        prompt = f"""Translate the following note to {target_language}. Return ONLY a JSON object with the translated fields. Do not add any explanation or markdown formatting.

Title: {title}
Content: {content}
Tags: {tags}

Return format:
{{"title": "translated title", "content": "translated content", "tags": "translated tags"}}"""
        
        client = get_openai_client()
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the given text to {target_language}. Return only valid JSON without any markdown formatting or code blocks.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.3,
            model="gpt-4o-mini",
        )
        
        # Parse the response
        import json
        translated_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if translated_text.startswith('```'):
            lines = translated_text.split('\n')
            translated_text = '\n'.join(lines[1:-1])
        
        translated_data = json.loads(translated_text)
        
        return jsonify({
            'title': translated_data.get('title', title),
            'content': translated_data.get('content', content),
            'tags': translated_data.get('tags', tags)
        })
        
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

