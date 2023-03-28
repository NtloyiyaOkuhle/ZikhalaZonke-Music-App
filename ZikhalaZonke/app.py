from flask import Flask, render_template, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
from flask_uploads  import UploadSet, configure_uploads, AUDIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music.db'
app.config['UPLOADED_AUDIO_DEST'] = 'static/audio'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

audio_files = UploadSet('audio', AUDIO)
configure_uploads(app, audio_files)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    songs = db.relationship('Song', backref='user', lazy=True)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, default=0)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    songs = Song.query.all()
    return render_template('home.html', songs=songs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already taken!')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('upload'))
        flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'audio' in request.files:
        title = request.form['title']
        artist = request.form['artist']
        filename = audio_files.save(request.files['audio'])
        new_song = Song(title=title, artist=artist, filename=filename, user=current_user)
        db.session.add(new_song)
        db.session.commit()
        flash('Song uploaded successfully!')
        return redirect(url_for('my_songs'))
    return render_template('upload.html')


@app.route('/my-songs')
@login_required
def my_songs():
    songs = current_user.songs
    return render_template('my_songs.html', songs=songs)
    
    
@app.route('/rate-song', methods=['POST'])
@login_required
def rate_song():
    song_id = request.form['song_id']
    rating = request.form['rating']
    song = Song.query.get(song_id)
    if song:
        # Check if the user has already rated the song
        existing_rating = Rating.query.filter_by(song_id=song_id, user_id=current_user.id).first()
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            db.session.commit()
        else:
            # Add new rating
            new_rating = Rating(song_id=song_id, user_id=current_user.id, rating=rating)
            db.session.add(new_rating)
            db.session.commit()
        flash('Song rated successfully!')
    else:
        flash('Invalid song!')
    return redirect(url_for('home'))

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    songs = Song.query.filter(Song.title.like(f'%{keyword}%') | Song.artist.like(f'%{keyword}%')).all()
    return render_template('search_results.html', songs=songs)

if __name__=='__main__':
    app.run(debug=True)