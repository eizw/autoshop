import flask
import json

app = flask.Flask(__name__)
app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

all_items = {}
f = open('items.json')
all_items = json.load(f)

@app.route('/')
def main():
    return flask.render_template("index.html")

@app.route('/items')
def item_list():
    query = flask.request.args.get('category', '')
    categories = all_items.keys()
    if query:
        items = all_items[query]
    else:
        items = sum(all_items.values(), [])

    return flask.render_template("item_list.html", 
        items=items,
        categories=categories,
        current_category=query,
    )

if __name__ == '__main__':
    app.run(debug=True)