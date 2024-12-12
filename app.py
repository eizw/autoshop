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
app.secret_key = 'your_secret_key'  # For session management

# Temporary in-memory storage for user credentials
users = {}

all_items = {}
f = open('items.json')
all_items_with_categories = json.load(f)
all_items = []
for cat in all_items_with_categories.values():
    for i in cat:
        all_items.append(i)

llm = genai.GenerativeModel("gemini-1.5-flash")
preset_msg = "You are a shop assistant in a store with the following items: " + ', '.join(
    [i['name'] for i in all_items]) + ". Help the user based on what they need."


# Routes
@app.route('/')
def main():
    user = flask.session.get('user')
    print(user)
    return flask.render_template("index.html", user=user)


@app.route('/chat', methods=['POST'])
def chat_with_bot():
    request = flask.request
    user = flask.session.get('user')
    if not user:
        return flask.redirect(flask.url_for('login'))  # Redirect if not logged in

    if request.method == "POST":
        data = request.form
        q = data.get('user_query', "")

        if "user_voice" in data:
            print("voice input")
            if "voice_query" not in request.files:
                return flask.render_template("chat.html", prev="Audio file not found")

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
        print(res.text)

        return flask.render_template("chat.html",
                                     prev=q,
                                     response=markdown.markdown(res.text),
                                     user=user
                                     )


@app.route('/items')
def item_list():
    user = flask.session.get('user')
    if not user:
        return flask.redirect(flask.url_for('login'))  # Redirect if not logged in

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
                                 user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        email = flask.request.form['email']
        password = flask.request.form['password']
        print(email, password, users[email])
        if email in users and users[email]['password'] == password:
            flask.session['user'] = {
                'name': users[email]['name'],
                'email': email,
            }  # Store email in session
            flask.flash('Login successful!', 'success')
            return flask.redirect(flask.url_for('main'))
        flask.flash('Invalid email or password', 'danger')
    return flask.render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if flask.request.method == 'POST':
        email = flask.request.form['email']
        password = flask.request.form['password']
        name = flask.request.form['name']
        if email in users:
            flask.flash('Email already registered!', 'danger')
        else:
            users[email] = {'password': password, 'name': name}  # Add new user to the dictionary
            flask.flash('Registration successful! Please log in.', 'success')
            return flask.redirect(flask.url_for('login'))
    return flask.render_template('register.html')


@app.route('/logout')
def logout():
    flask.session.pop('user', None)
    flask.flash('You have been logged out.', 'info')
    return flask.redirect(flask.url_for('main'))


if __name__ == '__main__':
    app.run(debug=True)
