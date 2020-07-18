#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from datetime import datetime
import sys
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database DONE
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(), default='')
    shows = db.relationship('Shows', backref='venues', cascade= 'all, delete-orphan', lazy=True )
    def __repr__(self):
        return f'<Venue: {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate DONE

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String, default='')
    shows =  db.relationship('Shows', backref='artist', cascade= 'all, delete-orphan', lazy=True)
    def __repr__(self):
        return f'<Artist: {self.id} {self.name}>'


    # TODO: implement any missing fields, as a database migration using Flask-Migrate DONE

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Shows(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable = False)

#shows = db.Table('shows',
#    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id')),
#    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id')),
#    db.Column('start_time', db.DateTime, nullable=False)
#)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = db.session.query(Venue.city, Venue.state).distinct() # different locations are listed
  data = []
  for area in areas:
    area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venue_data = []
    for venue in area_venues:
      venue_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": Shows.query.filter(Shows.venue_id==venue.id).filter(Shows.start_time>datetime.now()).count()
      })
    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venue_data
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  data = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all() #case insenstive query of venue table for name like search term
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  shows_data = Shows.query.filter_by(venue_id = venue_id) #query to get all shows in venue
  past_shows = []
  upcoming_shows  = []
  for s in shows_data:
      if s.start_time < datetime.now(): # get past shows
          artist = Artist.query.get(s.artist_id)# query artist table using artist_id from shows to get artist information
          past_shows.append({
             "artist_id": artist.id,
             "artist_name": artist.name,
             "artist_image_link": artist.image_link,
             "start_time": str(s.start_time)
          })
      else: # rest of shows are future shows
          artist = Artist.query.get(s.artist_id)
          upcoming_shows.append({
             "artist_id": artist.id,
             "artist_name": artist.name,
             "artist_image_link": artist.image_link,
             "start_time": str(s.start_time)
          })
  data = {
     "id": venue.id,
     "name": venue.name,
     "genres": venue.genres,
     "address": venue.address,
     "city": venue.city,
     "state": venue.state,
     "phone": venue.phone,
     "website": venue.website,
     "facebook_link": venue.facebook_link,
     "seeking_talent": venue.seeking_talent,
     "seeking_description": venue.seeking_description,
     "image_link": venue.image_link,
     "past_shows": past_shows,
     "upcoming_shows": upcoming_shows,
     "past_shows_count": len(past_shows),
     "upcoming_shows_count": len(upcoming_shows)
    }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form.get('name','')
    city = request.form.get('city','')
    state = request.form.get('state','')
    address = request.form.get('address','')
    phone = request.form.get('phone','')
    facebook_link = request.form.get('facebook_link','')
    genres = request.form.getlist('genres')
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, facebook_link=facebook_link, genres=genres)
    db.session.add(venue)
    db.session.commit()

  except:
     error = True
     db.session.rollback()
     print(sys.exc_info())
  finally:
     db.session.close()
     if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
     else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
         flash('An error occurred. Venue could not be deleted.')
      else:
         flash('Venue was successfully deleted!')
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data=Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  data = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all() #case insenstive query of artist table for name like search term
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  shows_data = Shows.query.filter_by(artist_id = artist_id) #query to get all shows for artist
  past_shows = []
  upcoming_shows  = []
  for s in shows_data:
      venue = Venue.query.get(s.venue_id)
      venue_detail = {
         "venue_id": venue.id,
         "venue_name": venue.name,
         "venue_image_link": venue.image_link,
         "start_time": str(s.start_time)
      }
      if s.start_time < datetime.now(): # get past shows
          past_shows.append(venue_detail)
      else: # rest of shows are future shows
          upcoming_shows.append(venue_detail)

  data = {
     "id": artist.id,
     "name": artist.name,
     "genres": artist.genres,
     "city": artist.city,
     "state": artist.state,
     "phone": artist.phone,
     "website": artist.website,
     "facebook_link":artist.facebook_link,
     "seeking_venue": artist.seeking_venue,
     "seeking_description": artist.seeking_description,
     "image_link": artist.image_link,
     "past_shows": past_shows,
     "upcoming_shows": upcoming_shows,
     "past_shows_count": len(past_shows),
     "upcoming_shows_count": len(upcoming_shows)
    }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form.get('name','')
      artist.city = request.form.get('city','')
      artist.state = request.form.get('state','')
      artist.phone = request.form.get('phone','')
      artist.facebook_link = request.form.get('facebook_link','')
      artist.genres = request.form.getlist('genres')
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
         flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
      else:
         flash('Artist ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue=Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
      venue = Venue.query.get(venue_id)
      venue.name = request.form.get('name','')
      venue.city = request.form.get('city','')
      venue.state = request.form.get('state','')
      venue.address = request.form.get('address','')
      venue.phone = request.form.get('phone','')
      venue.facebook_link = request.form.get('facebook_link','')
      venue.genres = request.form.getlist('genres')
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
         flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
      else:
         flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

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
      name = request.form.get('name','')
      city = request.form.get('city','')
      state = request.form.get('state','')
      phone = request.form.get('phone','')
      facebook_link = request.form.get('facebook_link','')
      genres = request.form.getlist('genres')
      artist = Artist(name=name, city=city, state=state, phone=phone, facebook_link=facebook_link, genres=genres)
      db.session.add(artist)
      db.session.commit()
    except:
       error = True
       db.session.rollback()
       print(sys.exc_info())
    finally:
       db.session.close()
    if error:
       flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
       flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  show_data = Shows.query.all()
  data = []
  for s in show_data:
      venue = Venue.query.get(s.venue_id)
      artist = Artist.query.get(s.artist_id)
      data.append({
        "venue_id": venue.id,
        "venue_name": venue.name,
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(s.start_time)
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    date_format = '%Y-%m-%d %H:%M:%S'
    try:
      artist_id = request.form.get('artist_id')
      venue_id = request.form.get('venue_id')
      start_time = datetime.strptime(request.form.get('start_time'), date_format) # converts string input from form to datetime
      show = Shows( start_time=start_time, artist_id=artist_id, venue_id=venue_id)
      db.session.add(show)
      db.session.commit()
    except:
       error = True
       db.session.rollback()
       print(sys.exc_info())
    finally:
       db.session.close()
    if error:
          flash('An error occurred. Show could not be listed.')
    else:
           flash('Show was successfully listed!')
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
