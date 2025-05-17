from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def create_chat_routes(app):
    @app.route('/api/ai/chat', methods=['POST'])
    def chat():
        try:
            message = request.json.get('message')
            
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for farmers. Please provide responses in Telugu language using Telugu script. Keep responses clear, concise, and farmer-friendly. If the input is in English, translate it to Telugu before processing and respond in Telugu. If the input is already in Telugu, respond in Telugu."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            ai_response = completion.choices[0].message.content

            return jsonify({
                "response": ai_response
            })
            
        except Exception as e:
            print('OpenAI API Error:', str(e))
            return jsonify({"error": "Failed to process your request"}), 500
