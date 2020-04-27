#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

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

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    seeking = db.Column(db.Boolean, nullable=False, default=False)
    seeking_message = db.Column(db.String(500))
    genres = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    website_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    seeking = db.Column(db.Boolean, nullable=False, default=False)
    seeking_message = db.Column(db.String(500))
    genres = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    website_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=False), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)

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


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data, locations = [], []
  venues = Venue.query.all()

  for venue in venues:
    if venue.city + "-" + venue.state not in locations:
      locations.append(venue.city + "-" + venue.state)

  for location in locations:
    data.append({
      "city": location.split("-")[0],
      "state": location.split("-")[1],
      "venues": []
    })

  for venue in venues:
    shows = Show.query.filter_by(venue_id=venue.id).all()
    num_shows = 0

    for show in shows:
      if show.date > datetime.now():
        num_shows += 1

    for item in data:
      if venue.city == item['city'] and venue.state == item['state']:
        item['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_shows
        })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')

  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": 0,
    "data": []
  }

  data = {}
  for venue in venues:
    upcoming_shows = 0
    shows = Show.query.filter_by(venue_id=venue.id).all()

    for show in shows:
      if show.date > datetime.now():
        upcoming_shows += 1

    data["id"] = venue.id
    data["name"] = venue.name
    data["num_upcoming_shows"] = upcoming_shows

    response["data"].append(data)
    response["count"] += 1

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres[1:-1].replace('"', '').split(","),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking,
    "seeking_description": venue.seeking_message,
    "image_link": venue.image_link,
    "past_shows_count": 0,
    "upcoming_shows_count": 0,
    "upcoming_shows": [],
    "past_shows": []
  }

  shows = Show.query.filter_by(venue_id=venue.id).all()
  for show in shows:
    artist = Artist.query.filter_by(id=show.artist_id).first()
    show_info = {
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": str(show.date)
    }

    if show.date > datetime.now():
      data["upcoming_shows"].append(show_info)
      data["upcoming_shows_count"] += 1
    else:
      data["past_shows"].append(show_info)
      data["past_shows_count"] += 1

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    form = VenueForm()

    name = form.name.data
    seeking = True if form.seeking.data == 'Yes' else False
    seeking_message = form.seeking_message.data
    genres = form.genres.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    website_link = form.website_link.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data

    venue = Venue(
        name=name, seeking=seeking, genres=genres, city=city, state=state, address=address,
        phone=phone, website_link=website_link, image_link=image_link, facebook_link=facebook_link,
        seeking_message=seeking_message
    )

    db.session.add(venue)
    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  name = venue.name

  try:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + name + ' was successfully removed from the system.')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' was not removed from the system.')
  finally:
    db.session.close()

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = Artist.query.all()
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')

  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": 0,
    "data": []
  }

  data = {}
  for artist in artists:
    upcoming_shows = 0
    shows = Show.query.filter_by(artist_id=artist.id).all()

    for show in shows:
      if show.date > datetime.now():
        upcoming_shows += 1

    data["id"] = artist.id
    data["name"] = artist.name
    data["num_upcoming_shows"] = upcoming_shows

    response["data"].append(data)
    response["count"] += 1

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres[1:-1].replace('"', '').split(","),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking,
    "seeking_description": artist.seeking_message,
    "image_link": artist.image_link,
    "past_shows_count": 0,
    "upcoming_shows_count": 0,
    "upcoming_shows": [],
    "past_shows": []
  }

  shows = Show.query.filter_by(artist_id=artist_id).all()
  for show in shows:
    venue = Venue.query.filter_by(id=show.venue_id).first()
    show_info = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": str(show.date)
    }

    if show.date > datetime.now():
      data["upcoming_shows"].append(show_info)
      data["upcoming_shows_count"] += 1
    else:
      data["past_shows"].append(show_info)
      data["past_shows_count"] += 1

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  data = Artist.query.filter_by(id=artist_id).first()
  artist = {
    "id": data.id,
    "name": data.name,
    "genres": data.genres[1:-1].replace('"', '').split(','),
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website_link": data.website_link,
    "facebook_link": data.facebook_link,
    "image_link": data.image_link,
    "seeking": data.seeking,
    "seeking_message": data.seeking_message,
  }

  form.state.process_data(artist['state'])
  form.genres.process_data(artist['genres'])
  form.seeking.process_data('Yes' if artist['seeking'] else 'No')
  form.seeking_message.process_data(artist['seeking_message'])

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()
    artist.name = form.name.data
    artist.seeking = True if form.seeking.data == 'Yes' else False
    artist.seeking_message = form.seeking_message.data
    artist.genres = form.genres.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website_link = form.website_link.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data

    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  data = Venue.query.filter_by(id=venue_id).first()
  venue = {
    "id": data.id,
    "name": data.name,
    "genres": data.genres[1:-1].replace('"', '').split(','),
    "city": data.city,
    "state": data.state,
    "address": data.address,
    "phone": data.phone,
    "website_link": data.website_link,
    "facebook_link": data.facebook_link,
    "image_link": data.image_link,
    "seeking": data.seeking,
    "seeking_message": data.seeking_message,
  }

  form.state.process_data(venue['state'])
  form.genres.process_data(venue['genres'])
  form.seeking.process_data('Yes' if venue['seeking'] else 'No')
  form.seeking_message.process_data(venue['seeking_message'])

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()
    venue.name = form.name.data
    venue.seeking = True if form.seeking.data == 'Yes' else False
    venue.seeking_message = form.seeking_message.data
    venue.genres = form.genres.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.website_link = form.website_link.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data

    print(venue)

    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    form = ArtistForm()

    name = form.name.data
    seeking = True if form.seeking.data == 'Yes' else False
    seeking_message = form.seeking_message.data
    genres = form.genres.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    website_link = form.website_link.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data

    artist = Artist(
      name=name, seeking=seeking, genres=genres, city=city, state=state, phone=phone,
      website_link=website_link, image_link=image_link, facebook_link=facebook_link,
      seeking_message=seeking_message
    )

    db.session.add(artist)
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  name = artist.name

  try:
    db.session.delete(artist)
    db.session.commit()
    flash('Artist ' + name + ' was successfully removed from the system.')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' was not removed from the system.')
  finally:
    db.session.close()

  return None

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows = Show.query.all()
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": format_datetime(str(show.date))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    form = ShowForm()

    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    show = Show(
      artist_id=artist_id, venue_id=venue_id, date=start_time,
    )

    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
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
