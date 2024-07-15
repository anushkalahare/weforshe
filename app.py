import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from datetime import datetime
import pandas as pd
import random
import json
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
from sqlalchemy import func

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "outfits.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    outfits = db.relationship('Outfit', backref='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Outfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    items = db.Column(db.PickleType, nullable=False)
    style = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='outfit', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfit.id'), nullable=False)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Load and preprocess data
csv_path = os.path.join(BASE_DIR, 'static', 'images_dataset', 'images.csv')
df = pd.read_csv(csv_path)

def standardize_file_path(file_path):
    return file_path.replace('C:/Outfit Builder/static/', '').replace('\\', '/')

# When reading the CSV file
df['File path'] = df['File path'].apply(standardize_file_path)

# Shuffle items once and store in a global variable
shuffled_items_by_type = {}
types = df['Type'].unique()
for t in types:
    type_items = df[df['Type'] == t].to_dict(orient='records')
    random.shuffle(type_items)
    shuffled_items_by_type[t] = type_items

# Helper functions
def get_most_reflected_style(selected_styles):
    style_counter = Counter(selected_styles)
    return style_counter.most_common(1)[0][0]

def analyze_overall_style_preference(outfits):
    all_styles = [outfit.style for outfit in outfits]
    style_counter = Counter(all_styles)
    most_frequent_style = style_counter.most_common(1)[0][0] if style_counter else None

    all_items = [item for outfit in outfits for item in outfit.items]
    item_counter = Counter(item['File path'] for item in all_items)
    most_frequent_image = item_counter.most_common(1)[0][0] if item_counter else None

    return most_frequent_style, most_frequent_image

def get_piechart_as_base64(data, title):
    plt.figure(figsize=(6, 6))
    plt.pie(list(data.values()), labels=list(data.keys()), autopct='%1.1f%%', startangle=90)
    plt.title(title)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# Routes
@app.route('/')
@login_required
def home():
    # Get trending outfits (most liked)
    trending_outfits = db.session.query(Outfit, func.count(Like.id).label('like_count')) \
        .join(Like) \
        .group_by(Outfit.id) \
        .order_by(func.count(Like.id).desc()) \
        .limit(10) \
        .all()

    # Get trending product images
    all_items = [item for outfit in Outfit.query.all() for item in outfit.items]
    item_counter = Counter(item['File path'] for item in all_items)
    trending_products = [{'file_path': file_path, 'count': count} 
                         for file_path, count in item_counter.most_common(10)]

    # Get all outfits for the horizontal scroll
    all_outfits = Outfit.query.order_by(Outfit.created_at.desc()).all()

    return render_template('home.html', 
                           trending_outfits=trending_outfits, 
                           trending_products=trending_products, 
                           all_outfits=all_outfits)

@app.route('/create_outfit')
@app.route('/create_outfit/<type>')
@login_required
def create_outfit(type='fullbody wear'):
    items_by_type = {}
    if type.capitalize() in shuffled_items_by_type:
        items_by_type[type.capitalize()] = [
            {**item, 'File path': standardize_file_path(item['File path'])}
            for item in shuffled_items_by_type[type.capitalize()]
        ]
    
    selected_items = request.args.get('selectedItems', '[]')
    try:
        selected_items = json.loads(selected_items)
    except json.JSONDecodeError:
        selected_items = []
    
    selected_items_info = [
        {
            'Srno': str(item['Srno']),
            'File path': standardize_file_path(item['File path']),
            'Style': item['Style'],
            'Type': item['Type']
        }
        for item in df[df['Srno'].isin([int(i) for i in selected_items])].to_dict('records')
    ]
    
    return render_template('create_outfit.html', 
                           items_by_type=items_by_type, 
                           selected_items=selected_items_info, 
                           current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Please use a different username.')
            return redirect(url_for('register'))
        user = User.query.filter_by(email=email).first()
        if user is not None:
            flash('Please use a different email address.')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    selected_items = json.loads(request.form['selectedItems'])
    outfit_title = request.form['outfitTitle']
    selected_styles = df[df['Srno'].isin([int(item) for item in selected_items])]['Style'].values
    
    most_reflected_style = get_most_reflected_style(selected_styles)
    
    selected_items_info = [
        {
            'Srno': str(item['Srno']),
            'File path': item['File path'],
            'Style': item['Style'],
            'Type': item['Type']
        }
        for item in df[df['Srno'].isin([int(i) for i in selected_items])].to_dict('records')
    ]
    
    new_outfit = Outfit(title=outfit_title, items=selected_items_info, style=most_reflected_style, user_id=current_user.id)
    db.session.add(new_outfit)
    db.session.commit()
    
    user_outfits = Outfit.query.filter_by(user_id=current_user.id).all()
    
    most_frequent_style, most_frequent_image = analyze_overall_style_preference(user_outfits)
    
    style_counts = {}
    type_counts = {}
    for outfit in user_outfits:
        style_counts[outfit.style] = style_counts.get(outfit.style, 0) + 1
        for item in outfit.items:
            item_type = item['Type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

    style_chart = get_piechart_as_base64(style_counts, 'Style Distribution')
    type_chart = get_piechart_as_base64(type_counts, 'Item Type Distribution')

    return render_template(
        'result.html', 
        style=most_reflected_style, 
        selected_items=selected_items_info,
        curated_fits=user_outfits,
        overall_style=most_frequent_style,
        overall_image=most_frequent_image,
        style_chart=style_chart,
        type_chart=type_chart
    )

@app.route('/like/<int:outfit_id>', methods=['POST'])
@login_required
def like_outfit(outfit_id):
    outfit = Outfit.query.get_or_404(outfit_id)
    if current_user.id == outfit.user_id:
        return jsonify({'error': 'You cannot like your own outfit'}), 400
    like = Like.query.filter_by(user_id=current_user.id, outfit_id=outfit.id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'likes': outfit.likes.count(), 'liked': False})
    else:
        like = Like(user_id=current_user.id, outfit_id=outfit.id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'likes': outfit.likes.count(), 'liked': True})

@app.route('/explore')
@login_required
def explore():
    outfits = Outfit.query.filter(Outfit.user_id != current_user.id).all()
    return render_template('explore.html', outfits=outfits)

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    outfits = user.outfits.order_by(Outfit.created_at.desc()).all()
    return render_template('profile.html', user=user, outfits=outfits)

@app.route('/outfit/<int:outfit_id>')
def outfit_detail(outfit_id):
    outfit = Outfit.query.get_or_404(outfit_id)
    return render_template('outfit_detail.html', outfit=outfit)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
