#Resources
#https://developers.themoviedb.org/3/search/search-movies
#https://docs.sqlalchemy.org/en/13/orm/query.html#sqlalchemy.orm.query.Query.order_by

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired
import requests
import os

API_KEY = os.environ["API_KEY"]
URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_URL = "https://api.themoviedb.org/3/movie"
IMG_URL = "https://www.themoviedb.org/t/p/w1280"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-list.db' #Creating the database

db = SQLAlchemy(app)

#Creating the table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True)
    year = db.Column(db.Integer)
    description = db.Column(db.String(250))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer, unique=True)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250))

with app.app_context():
    db.create_all()

#Creating rating and review form
class RatingForm(FlaskForm):
    rating = StringField(label="Your Rating Out of 10 e.g. 7.5", validators=[InputRequired("Please input new rating.")])
    review = StringField(label="Your Review", validators=[InputRequired("Please update review.")])
    submit = SubmitField(label="Done")

#Creating find movie form.
class FindMovie(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

#Creating homepage with movies ordered and ranked by rating.
@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)-i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

#Updating rating and review.
@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    rating_form = RatingForm()
    if rating_form.validate_on_submit():
        movie_selected.rating = float(rating_form.rating.data)
        movie_selected.review = rating_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=rating_form, movie=movie_selected)

#Deleting a movie from database.
@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for('home'))

#Adding movie to database using API
@app.route("/add", methods=["GET", "POST"])
def add():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        response = requests.get(url=f"{MOVIE_URL}/{movie_api_id}", params={'api_key': API_KEY})
        movie_data = response.json()
        new_movie = Movie(
            title = movie_data['original_title'],
            year = movie_data['release_date'].split("-")[0],
            description = movie_data['overview'],
            img_url = f"{IMG_URL}/{movie_data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))
    find_movie_form = FindMovie()
    if find_movie_form.validate_on_submit():
        movie_to_search = find_movie_form.title.data
        response = requests.get(url=URL, params={'api_key': API_KEY, 'query': movie_to_search})
        movies_tmdb = response.json()["results"]
        return render_template("select.html", options=movies_tmdb)
    return render_template("add.html", form=find_movie_form)

if __name__ == '__main__':
    app.run(debug=True)
