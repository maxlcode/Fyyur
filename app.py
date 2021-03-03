#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import tuple_, func
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm , Form
from flask_migrate import Migrate
from forms import *
from datetime import datetime
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


# New class Genre 
class Genre(db.Model):
    __tablename__ = 'Genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

#Mapping table between Artist and Genre (Many to Many)
artist_genre_table = db.Table('artist_genre',
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
)
#Mapping table between Venue and Genre (Many to Many)
venue_genre_table = db.Table('venue_genre',
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable= False)
    city = db.Column(db.String(120),nullable= False)
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship('Genre', secondary=venue_genre_table, backref=db.backref('venues'))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    def __repr__(self):
      return f'<id: {self.id}, name: {self.name}>'

   

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,nullable= False)
    city = db.Column(db.String(120),nullable= False)
    address = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.relationship('Genre', secondary=artist_genre_table, backref=db.backref('artists'))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    
    def __repr__(self):
       return f'<id: {self.id}, name: {self.name}>'

class Show(db.Model):
    __tablename__ ='Show'
    id = db.Column(db.Integer, primary_key=True)
    time= db.Column(db.DateTime())
    venue_id = db.Column (db.Integer,db.ForeignKey('Venue.id'),nullable = False)
    venue = db.relationship('Venue',backref=db.backref('shows'))
    artist_id = db.Column (db.Integer, db.ForeignKey('Artist.id'),nullable = False)
    artist = db.relationship('Artist',backref=db.backref('shows'))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  -----------------------------------------------
#  VENUES
#  ----------------------------------------------------------------
# Display Venues
# --------------------------------------
@app.route('/venues')
def venues():
  data=[]
  # Get all possible locations by city and state
  # Question: Why does distinct not work for both columns?
  venue_locations = Venue.query.distinct(Venue.city, Venue.state).all()
  # Loop through each location and query for the according venues
  for location in venue_locations:
      city = location.city
      state = location.state
      location_data = {
        "city": city, 
        "state": state, 
        "venues": []
      }
      # Filter now for all venues that belong to a city/state combination
      venues = Venue.query.filter_by(city=city, state=state).all()
      #loop through all venues and append name and id to data
      for venue in venues:
        venue_name = venue.name
        venue_id = venue.id
        venue_data = {
          "id": venue_id,
          "name": venue_name,
        }
        location_data["venues"].append(venue_data)
        #append to total data
        data.append(location_data)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form['search_term']
  venues = db.session.query(Venue).filter(Venue.name.ilike('%'+search+'%')).all()
  data = []
  # create file for all results
  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name,
      #"num_upcoming_shows": 0, len(db.session.query(Show).filter(Show.venue_id == v.id).filter(Show.start_time > datetime.now()).all()),
    })
  #create response message with count on results
  response={
    "count": len(venues),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  # If venue with this id is not existing, go to home and flash an error message
  if not venue:
     flash('Venue with ID ' + str(venue_id) + ' is not existing')
     return render_template('pages/home.html')
  else:
    #get name of genres
    genres = [ genre.name for genre in venue.genres ]
    #get current date + time
    current_time = datetime.now()
    #filter fo past shows                               
    past_shows = db.session.query(Show).join(Venue).filter(venue_id==Show.venue_id).filter(Show.time < current_time).all()
    #filter for upcoming shows
    upcoming_shows = db.session.query(Show).join(Venue).filter(venue_id==Show.venue_id).filter(Show.time > current_time).all()
    
    data={
      "id": venue.id,
      "name": venue.name,
      "genres": genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "facebook_link": venue.facebook_link,
      "past_shows":[],
      "upcoming_shows":[],
      "past_shows_count" : len(past_shows),
      "upcoming_shows_count" : len(upcoming_shows),
    }
    #add the data for past shows
    for show in past_shows:
        show_data = {
          "venue_id": show.artist.id,
          "venue_name": show.artist.name,
          "venue_image_link": show.artist.image_link,
          "start_time" : str(show.time),
        }
        data["past_shows"].append(show_data)
    #add the data for upcoming shows
    for show in upcoming_shows:
        show_data = {
          "venue_id": show.artist.id,
          "venue_name": show.artist.name,
          "venue_image_link": show.artist.image_link,
          "start_time" : str(show.time),
        }
        data["upcoming_shows"].append(show_data)

  return render_template('pages/show_venue.html', venue=data)

#  CREATE Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    
    facebook_link = request.form['facebook_link']
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, facebook_link=facebook_link)

    #Genre must be handled different because it is a list
    genres = request.form.getlist('genres')
    
    for genre in genres:
      #check if genre already existing
      genre_existing = Genre.query.filter_by(name=genre).one_or_none()  
      if genre_existing:
        #the genre is existing, just add to the list
        venue.genres.append(genre_existing)
      else:
        #create the genre item and append it
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        venue.genres.append(new_genre)  
    
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed')
    return render_template('pages/home.html')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


# Update Venue
# -----------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  genres = [ genre.name for genre in venue.genres ]
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "city": venue.city,
    "address": venue.address,
    "state": venue.state,
    "phone": venue.phone,
    "facebook_link": venue.facebook_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue_to_edit = Venue.query.get(venue_id)
  error = False
  try:
    venue_to_edit.name = request.form['name']
    venue_to_edit.state = request.form['state']
    venue_to_edit.city = request.form['city']
    venue_to_edit.phone = request.form['phone']
    venue_to_edit.facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    
    for genre in genres:
      #check if genre already existing
      genre_existing = Genre.query.filter_by(name=genre).one_or_none()  
      if genre_existing:
        #the genre is existing, just add to the list
        venue_to_edit.genres.append(genre_existing)
      else:
        #create the genre item and append it
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        venue_to_edit.genres.append(new_genre)  
    db.session.add(venue_to_edit)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated')
    return render_template('pages/home.html')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

# DELETE Venue
# ------------------------------------------------------
@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  body ={}
  error = False
  try:
    venue = Venue.query.get(venue_id)
    body['name'] = venue.name
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occured. Please try again')
    return render_template('pages/home.html')
  else:
    flash('Venue ' + body['name'] + ' was successfully deleted!')
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------

# Display Artists
# --------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.order_by(Artist.name).all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = request.form['search_term']
  artists = db.session.query(Artist).filter(Artist.name.ilike('%'+search+'%')).all()
  data = []
  # create file for all results
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
      #"num_upcoming_shows": 0, len(db.session.query(Show).filter(Show.venue_id == v.id).filter(Show.start_time > datetime.now()).all()),
    })
  #create response message with count on results
  response={
    "count": len(artists),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # Search for item by primary key ID in database
  artist = Artist.query.get(artist_id)
  # If artist with this id is not existing, go to home a flash message
  if not artist:
     flash('Artist with ID ' + str(artist_id) + ' is not existing')
     return render_template('pages/home.html')
  else:
    # get genre names
    genres = [ genre.name for genre in artist.genres ]
    # get all shows of the artist
    shows = db.session.query(Show).filter_by(artist_id=artist_id)
    # get current date + time
    current_time = datetime.now()
    # filter fo past shows                              
    past_shows = db.session.query(Show).join(Venue).filter(artist_id==Show.artist_id).filter(Show.time < current_time).all()
    #filter for upcoming shows
    upcoming_shows = db.session.query(Show).join(Venue).filter(artist_id==Show.artist_id).filter(Show.time > current_time).all()
    #Create data
    data={
      "id": artist.id,
      "name": artist.name,
      "genres": genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": 'n/a',
      "facebook_link": artist.facebook_link,
      "past_shows":[],
      "upcoming_shows":[],
      "past_shows_count" : len(past_shows),
      "upcoming_shows_count" : len(upcoming_shows),
    }
    #add the data for past shows
    for show in past_shows:
        show_data = {
          "venue_id": show.venue.id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time" : str(show.time),
        }
        data["past_shows"].append(show_data)
    #add the data for upcoming shows
    for show in upcoming_shows:
        show_data = {
          "venue_id": show.venue.id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time" : str(show.time),
        }
        data["upcoming_shows"].append(show_data)

  return render_template('pages/show_artist.html', artist=data)

#  Update Artists
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  genres = [ genre.name for genre in artist.genres ]
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
  }
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist_to_edit = Artist.query.get(artist_id)
  error = False
  try:
    artist_to_edit.name = request.form['name']
    artist_to_edit.state = request.form['state']
    artist_to_edit.city = request.form['city']
    artist_to_edit.phone = request.form['phone']
    artist_to_edit.facebook_link = request.form['facebook_link']

    genres = request.form.getlist('genres')
    
    for genre in genres:
      #check if genre already existing
      genre_existing = Genre.query.filter_by(name=genre).one_or_none()  
      if genre_existing:
        #the genre is existing, just add to the list
        artist_to_edit.genres.append(genre_existing)
      else:
        #create the genre item and append it
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        artist_to_edit.genres.append(new_genre)  

    db.session.add(artist_to_edit)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated')
    return render_template('pages/home.html')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    facebook_link = request.form['facebook_link']
    artist = Artist(name=name, city=city, state=state, phone=phone, facebook_link=facebook_link)

    genres = request.form.getlist('genres')
    
    for genre in genres:
      #check if genre already existing
      genre_existing = Genre.query.filter_by(name=genre).one_or_none()  
      if genre_existing:
        #the genre is existing, just add to the list
        artist.genres.append(genre_existing)
      else:
        #create the genre item and append it
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        artist.genres.append(new_genre)  

    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed')
    return render_template('pages/home.html')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

#  Delete Artist
#  --------------------------------------------------
@app.route('/artists/<int:artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
  body ={}
  error = False
  try:
    artist = Artist.query.get(artist_id)
    body['name'] = artist.name
    db.session.delete(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Artist could not be deleted! Try again')
    return render_template('pages/home.html')
  else:
    flash('Artist ' + body['name'] + ' was successfully deleted!')
    return render_template('pages/home.html')
    

#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  data=[]
  shows=Show.query.all()
  for show in shows:
    show_data ={
    "venue_id": show.venue.id,
    "venue_name": show.venue.name,
    "artist_id": show.artist.id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": str(show.time),
    }
    data.append(show_data)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET'])
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    time= request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id, time=time)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be created. Please try again')
    return render_template('pages/home.html')
  else:
    flash('Show was successfully created!')
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
