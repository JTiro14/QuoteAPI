from flask import Flask, jsonify, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import random
from dotenv import load_dotenv, find_dotenv
import os

app = Flask(__name__)

# load environment variables
load_dotenv(find_dotenv())

# api-key
API_KEY = os.environ.get('API_KEY')

# connect to DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///quotes.db')
db = SQLAlchemy()
db.init_app(app)


# Quote DB Configuration
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()

    # with open('quotes.txt') as file:
    #     quotes = file.readlines()
    #
    # for quote_line in quotes:
    #     # Split the line into quote and author using '~'
    #     quote_split = quote_line.strip().split('~')
    #
    #     # Ensure that the split result contains both quote and author
    #     if len(quote_split) == 2:
    #         # Extract the quote by removing double quotes
    #         quote_clean = quote_split[0].strip().strip('"')
    #
    #         # Extract the author
    #         author_clean = quote_split[1].strip()
    #
    #         # Create a new Quote instance
    #         new_quote = Quote(
    #             quote=quote_clean,
    #             author=author_clean
    #         )
    #
    #         # Add the new quote to the session
    #         db.session.add(new_quote)
    #
    # # Commit changes outside the loop to improve performance
    # db.session.commit()
    #
    # print('Success')


@app.route('/')
def home():
    return render_template('index.html')


# get random quote
@app.route('/random')
def get_random_quote():
    quotes = db.session.execute(db.select(Quote)).scalars().all()
    random_quote = random.choice(quotes)
    random_quote_dict = {
        'quote': {
            'quote': random_quote.quote,
            'author': random_quote.author
        }
    }

    response = jsonify(random_quote_dict)
    return response


# get all quotes
@app.route('/all')
def get_all_quotes():
    quotes = db.session.execute(db.select(Quote)).scalars().all()
    quotes_dict = [
        {
            'quote': quote.quote,
            'author': quote.author
        } for quote in quotes]

    response = jsonify({'quotes': quotes_dict})
    return response


# search quote/s by author
@app.route('/search')
def quote_author():
    query_author = request.args.get('author').title()
    result = db.session.execute(db.select(Quote).where(Quote.author == query_author)).scalars().all()
    if result:
        quotes_dict = [
            {
                'quote': quote.quote,
                'author': quote.author
            } for quote in result]
        response = jsonify({'quote': quotes_dict})
    else:
        error = {
            'error': {
                'Not Found': "Sorry, we don't have cafe at that location."
            }
        }
        response = jsonify(error)
    return response


# HTTP POSt - add quote
@app.route('/add', methods=['POST'])
def post_new_quote():
    api_key_params = request.args.get("api-key")
    if api_key_params == API_KEY:
        try:
            new_quote = Quote(
                quote=request.form.get('quote'),
                author=request.form.get('author'),
            )
            db.session.add(new_quote)
            db.session.commit()
            return jsonify(response={"Success": "Successfully added the new cafe."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(error={"Message": f"Failed to add the new quote. Error: {str(e)}"}), 500
    else:
        return jsonify(
            error={"Not Authorised": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403


# HTTP DELETE = Delete Quote
@app.route('/delete/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    api_key_params = request.args.get("api-key")
    if api_key_params == API_KEY:
        quote_to_delete = db.session.execute(db.select(Quote).where(Quote.id == quote_id)).scalar()
        if quote_to_delete:
            db.session.delete(quote_to_delete)
            db.session.commit()
            return jsonify(success={"Success": "Successfully deleted the quote."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a quote with that id was not found in the database."}), 404
    else:
        return jsonify(
            error={"Not Authorised": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403


# HTTP PUT/PATCH - Edit/Update Quote
@app.route('/update-quote/<int:quote_id>', methods=['PATCH'])
def update_quote(quote_id):
    api_key_params = request.args.get("api-key")
    if api_key_params == API_KEY:
        new_quote = request.args.get('new_quote')
        new_author = request.args.get('new_author')
        quote_to_update = db.session.get(Quote, quote_id)
        if quote_to_update:
            quote_to_update.quote = new_quote
            quote_to_update.author = new_author
            db.session.commit()
            return jsonify(response={"Success": "Successfully updated the quote."}), 200
        else:
            return jsonify(error={"Error": {"Not Found": "Sorry a quote with that id was not found in the database."}}), 404
    else:
        return jsonify(
            error={"Not Authorised": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403


if __name__ == "__main__":
    app.run(debug=False, port=5012)