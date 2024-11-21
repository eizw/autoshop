import flask
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import markdown
import speech_recognition as sr

load_dotenv()
LLAMA_API_KEY = os.getenv('LLAMA_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


genai.configure(api_key=GEMINI_API_KEY)

app = flask.Flask(__name__)
app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

all_items = {}
f = open('items.json')
all_items_with_categories = json.load(f)
all_items = []
for cat in all_items_with_categories.values():
    for i in cat:
        all_items.append(i)

llm = genai.GenerativeModel("gemini-1.5-flash")
preset_msg = "You are a shop assistant in a store with the following items: " + ', '.join([i['name'] for i in all_items]) + ". Help the user based on what he needs."
# print(sum([i.name for i in ], []))

@app.route('/')
def main():
    return flask.render_template("index.html")

@app.route('/api/chat', methods=['POST'])
def chat_with_bot():
    request = flask.request
    if request.method == "POST":
        data = request.form
        q = data.get('user_query', "")
        print(request.files)

        if "user_voice" in data:
            print("voice input")
            if "voice_query" not in request.files:
                return flask.render_template("chat.html",
                                                prev="Audio file not found"
                                            )
            
            file = request.files["voice_query"]
            if file.filename == "":
                return flask.redirect(request.url)
            print(file)
                
            if file:
                recognizer = sr.Recognizer()
                audioFile = sr.AudioFile(file)
                with audioFile as source:
                    data = recognizer.record(source)
                print(data)
                
                try:
                    q = recognizer.recognize_google(data, key=None)
                    print(q)
                except:
                    return {"status": 403, "message": "Google Speech Recognition could not understand audio."}
            return {"status": 200, "message": q}
        
        msg = preset_msg + q
        res = llm.generate_content(msg)

        return flask.render_template("chat.html",
            prev=q,
            response=markdown.markdown(res.text),                             
        )

@app.route('/items')
def item_list():
    query = flask.request.args.get('category', '')
    categories = all_items_with_categories.keys()
    if query:
        items = all_items_with_categories[query]
    else:
        items = all_items

    return flask.render_template("item_list.html", 
        items=items,
        categories=categories,
        current_category=query,
    )

if __name__ == '__main__':
    app.run(debug=True)