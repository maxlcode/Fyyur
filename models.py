from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# New class Genre 
class Genre(db.Model):
    __tablename__ = 'Genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    pass
#Mapping table between Artist and Genre (Many to Many)
artist_genre_table = db.Table('artist_genre',
  db.Column('genre_id', 
            db.Integer, 
            db.ForeignKey('Genre.id'), 
            primary_key=True
            ),
  db.Column('artist_id', 
            db.Integer, 
            db.ForeignKey('Artist.id'),
            primary_key=True
            )
)
#Mapping table between Venue and Genre (Many to Many)
venue_genre_table = db.Table('venue_genre',
  db.Column('genre_id', 
            db.Integer, 
            db.ForeignKey('Genre.id'),
            primary_key=True
            ),
  db.Column('venue_id', 
            db.Integer,
            db.ForeignKey('Venue.id'), 
            primary_key=True
            )
)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable= False)
    city = db.Column(db.String(120),nullable= False)
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship('Genre', 
                            secondary=venue_genre_table, 
                            backref=db.backref('venues')
                            )
    seeking = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    def __repr__(self):
      return f'<id: {self.id}, name: {self.name}>'
    pass
   

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,nullable= False)
    city = db.Column(db.String(120),nullable= False)
    address = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.relationship('Genre', 
                            secondary=artist_genre_table, 
                            backref=db.backref('artists')
                            )
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    def __repr__(self):
       return f'<id: {self.id}, name: {self.name}>'
    pass

class Show(db.Model):
    __tablename__ ='Show'
    id = db.Column(db.Integer, primary_key=True)
    time= db.Column(db.DateTime())
    venue_id = db.Column (db.Integer,
                        db.ForeignKey('Venue.id'),
                        nullable = False
                        )
    venue = db.relationship('Venue',backref=db.backref('shows'))
    artist_id = db.Column (db.Integer, 
                        db.ForeignKey('Artist.id'),
                        nullable = False
                        )
    artist = db.relationship('Artist',backref=db.backref('shows'))
    pass
