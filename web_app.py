from flask import Flask, request, jsonify, render_template
import openai
import re
import requests

app = Flask(__name__)

# Set up OpenAI API key
openai.api_key = "YOUR-API-KEY"

chat_sessions = {}

def generate_response(conversation_history, api_base, model):
    openai.api_base = api_base
    response = openai.ChatCompletion.create(
        model=model,
        messages=conversation_history
    )
    return response['choices'][0]['message']['content']

def generate_image(prompt):
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['data'][0]['url']
    else:
        return "Error generating image"

def format_response(response_text):
    def highlight_code_blocks(text):
        code_block_pattern = re.compile(r'```(.*?)\n(.*?)```', re.DOTALL)
        
        def replace_code_block(match):
            language, code = match.groups()
            language = language.strip()
            code = code.strip()
            if language == 'python':
                class_ = 'language-python'
            elif language == 'bash':
                class_ = 'language-bash'
            else:
                class_ = 'language-text'
            highlighted_code = f'<pre><code class="{class_}">{code}</code><button class="copy-button">Copy</button></pre>'
            return highlighted_code

        text = re.sub(code_block_pattern, replace_code_block, text)
        return text

    response_text = highlight_code_blocks(response_text)
    
    response_text = re.sub(r'`(pip install [\w-]+)`', r'<span class="command-line">\1</span>', response_text)
    
    response_text = re.sub(r'(\d+\.\s)', r'<br>\1', response_text)

    return response_text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/bot', methods=['POST'])
def bot():
    data = request.get_json()
    message = data.get('message')
    session_id = data.get('session_id')
    conversation_history = data.get('history', [])
    api_base = data.get('api_base', 'https://api.openai.com/v1')
    model = data.get('model', 'gpt-3.5-turbo')

    if model == "dall-e-3":
        return bot_dall_e_3_internal(data)

    conversation_history.append({"role": "user", "content": message})
    response_text = generate_response(conversation_history, api_base, model)
    conversation_history.append({"role": "assistant", "content": response_text})

    formatted_response_text = format_response(response_text)

    response = {'response': formatted_response_text, 'session_id': session_id}

    return jsonify(response)

@app.route('/bot-gpt4o', methods=['POST'])
def bot_gpt4o():
    data = request.get_json()
    message = data.get('message')
    session_id = data.get('session_id')
    conversation_history = data.get('history', [])
    api_base = data.get('api_base', 'https://api.openai.com/v1')

    conversation_history.append({"role": "user", "content": message})
    response_text = generate_response(conversation_history, api_base, "gpt-4o")
    conversation_history.append({"role": "assistant", "content": response_text})

    formatted_response_text = format_response(response_text)

    response = {'response': formatted_response_text, 'session_id': session_id}
    return jsonify(response)

@app.route('/bot-dall-e-3', methods=['POST'])
def bot_dall_e_3():
    data = request.get_json()
    return bot_dall_e_3_internal(data)

def bot_dall_e_3_internal(data):
    message = data.get('message')
    session_id = data.get('session_id')

    image_url = generate_image(message)
    response = {'image_url': image_url, 'session_id': session_id}

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Bind to all interfaces for public access
