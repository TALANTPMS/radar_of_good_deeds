from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import os
try:
    from dotenv import load_dotenv
    load_dotenv()  # загружаем переменные окружения из .env
except ImportError:
    print("python-dotenv not installed, skipping .env loading")
import logging
from logging.handlers import RotatingFileHandler
import sys
from sqlalchemy.exc import SQLAlchemyError

# Обновляем путь к шаблонам и статическим файлам
app = Flask(__name__)

# Обновляем конфигурацию БД для локального запуска
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'KAPIBARA2025SKANAPP'

# Настройка базы данных
if os.environ.get('VERCEL_ENV') == 'production':
    DATABASE_URL = os.environ.get('POSTGRES_URL')
    if DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Обновляем конфигурацию БД для работы на Vercel
if os.environ.get('VERCEL_ENV') == 'production':
    # Используем SQLite для демонстрации, в продакшене лучше использовать PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настраиваем пути к шаблонам и статическим файлам для Vercel
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Фиктивный словарь для определения координат по городу (прототип)
CITY_COORDINATES = {
    # Города Казахстана
    "алматы": (43.238949, 76.889709),
    "алмата": (43.238949, 76.889709),
    "астана": (51.1605, 71.4704),
    "нур-султан": (51.1605, 71.4704),
    "нур султан": (51.1605, 71.4704),
    "шымкент": (42.3417, 69.5901),
    "караганда": (49.8065, 73.0871),
    "таразы": (42.9046, 71.3894),
    "уст-каменогорск": (49.9761, 82.6061),
    "павлодар": (52.2833, 76.9667),
    "костанай": (53.222, 63.619),
    "аттырау": (47.1308, 51.9234),
    "уральск": (51.2401, 51.2012),
    "актау": (44.9989, 51.8892),

    # Популярные города России
    "москва": (55.7558, 37.6176),
    "санкт-петербург": (59.9311, 30.3609),
    "новосибирск": (55.0084, 82.9357),
    "екатеринбург": (56.8389, 60.6057),
    "казань": (55.8304, 49.0661),
    "самара": (53.1959, 50.1000),
    "омск": (54.9893, 73.3682),
    "челябинск": (55.1644, 61.4368),
    "ростов-на-дону": (47.2357, 39.7015),
    "уфа": (54.7388, 55.9721),
    "волгоград": (48.7080, 44.5133),
    "краснодар": (45.0443, 38.9760),
    "воронеж": (51.6615, 39.2003),
    "нижний новгород": (56.2965, 43.9361),
    "пермь": (58.0000, 56.2500)
}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    city = db.Column(db.String(100))  # теперь только город
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    markers = db.relationship('Marker', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    help_needed = db.Column(db.String(200), nullable=False)
    offer = db.Column(db.String(200))
    location_text = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    comments = db.relationship('Comment', backref='marker', lazy=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marker_id = db.Column(db.Integer, db.ForeignKey('marker.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Change root route to redirect to login
@app.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('map_view'))
    return redirect(url_for('login'))


# Главная страница – карта с метками
@app.route('/map')
@login_required
def map_view():
    markers = Marker.query.filter(Marker.deadline >= datetime.today().date()).all()
    center_lat = current_user.lat if current_user.lat is not None else 55.7558
    center_lng = current_user.lng if current_user.lng is not None else 37.6176
    return render_template('index.html', markers=markers, center_lat=center_lat, center_lng=center_lng, user=current_user)


# Страница объявлений
@app.route('/announcements')
@login_required
def announcements():
    q = request.args.get('q', '')
    markers = Marker.query.filter(Marker.deadline >= datetime.today().date()).all()
    if q:
        markers = [m for m in markers if q.lower() in m.location_text.lower() or q.lower() in m.help_needed.lower()]
    return render_template('announcements.html', markers=markers, query=q, user=current_user)


# Детали объявления
@app.route('/announcement/<int:marker_id>')
@login_required
def announcement(marker_id):
    marker = Marker.query.get_or_404(marker_id)
    return render_template('announcement.html', marker=marker, user=current_user)


# Обновление местоположения (только город)
@app.route('/location', methods=['GET', 'POST'])
@login_required
def location():
    if request.method == 'POST':
        city = request.form.get('city', '').strip().lower()
        coords = CITY_COORDINATES.get(city, (51.1605, 71.4704))
        current_user.city = city
        current_user.lat, current_user.lng = coords
        db.session.commit()
        flash('Местоположение обновлено', 'success')
        return redirect(url_for('map_view'))
    return render_template('location.html', user=current_user)


# Страница рейтингов
@app.route('/rating')
@login_required
def rating():
    top_announcements = User.query.outerjoin(Marker).group_by(User.id).order_by(db.func.count(Marker.id).desc()).limit(100).all()
    top_feedback = User.query.outerjoin(Comment).group_by(User.id).order_by(db.func.count(Comment.id).desc()).limit(100).all()
    return render_template('rating.html', top_announcements=top_announcements, top_feedback=top_feedback, user=current_user)


# Страница "О проекте"
@app.route('/about')
def about():
    return render_template('about.html', user=current_user if current_user.is_authenticated else None)


# Поиск объявлений и пользователей
@app.route('/search')
@login_required
def search():
    q = request.args.get('q', '')
    users_found = User.query.filter(User.username.contains(q)).all()
    markers_found = Marker.query.filter(Marker.location_text.contains(q)).all()
    return render_template('search.html', q=q, users_found=users_found, markers_found=markers_found, user=current_user)


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('map_view'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('map_view'))
        else:
            flash('Неправильное имя пользователя или пароль', 'danger')
    return render_template('login.html')


# Регистрация – теперь поле местоположения только город
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('map_view'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        city = request.form.get('city', '')
        coords = CITY_COORDINATES.get(city.strip().lower(), (55.7558, 37.6176))
        if User.query.filter_by(username=username).first():
            flash('Пользователь уже существует!', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, city=city, lat=coords[0], lng=coords[1])
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы!', 'success')
    return redirect(url_for('login'))


# Добавление метки (AJAX)
@app.route('/add_marker', methods=['POST'])
@login_required
def add_marker():
    data = request.get_json()
    try:
        marker = Marker(
            user_id=current_user.id,
            help_needed=data['help_needed'],
            offer=data.get('offer', ''),
            location_text=data['location'],
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d').date(),
            contact=data['contact'],
            latitude=float(data['lat']),
            longitude=float(data['lng'])
        )
        db.session.add(marker)
        db.session.commit()
        return jsonify({'status': 'success', 'marker_id': marker.id})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding marker: {str(e)}')
        return jsonify({'status': 'error', 'error': 'Internal Server Error'}), 500


# Редактирование метки (AJAX)
@app.route('/edit_marker', methods=['POST'])
@login_required
def edit_marker():
    data = request.get_json()
    try:
        marker = Marker.query.get(data['marker_id'])
        if marker and marker.user_id == current_user.id:
            marker.help_needed = data.get('help_needed', marker.help_needed)
            marker.offer = data.get('offer', marker.offer)
            marker.location_text = data.get('location', marker.location_text)
            marker.deadline = datetime.strptime(data.get('deadline', marker.deadline.strftime('%Y-%m-%d')), '%Y-%m-%d').date()
            marker.contact = data.get('contact', marker.contact)
            db.session.commit()
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'error': 'Нет доступа или метка не найдена'}), 403
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error editing marker: {str(e)}')
        return jsonify({'status': 'error', 'error': 'Internal Server Error'}), 500


# Удаление метки (AJAX)
@app.route('/delete_marker', methods=['POST'])
@login_required
def delete_marker():
    data = request.get_json()
    try:
        marker = Marker.query.get(data['marker_id'])
        if marker and marker.user_id == current_user.id:
            db.session.delete(marker)
            db.session.commit()
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'error': 'Нет доступа или метка не найдена'}), 403
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting marker: {str(e)}')
        return jsonify({'status': 'error', 'error': 'Internal Server Error'}), 500


# Добавление комментария (AJAX)
@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    data = request.get_json()
    try:
        comment = Comment(
            marker_id=data['marker_id'],
            user_id=current_user.id,
            text=data['text']
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({'status': 'success', 'comment_id': comment.id})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding comment: {str(e)}')
        return jsonify({'status': 'error', 'error': 'Internal Server Error'}), 500


# Улучшенная настройка логирования с проверкой прав доступа
def setup_logging(app):
    log_dir = 'logs'
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, 'good_deeds.log')
        
        # Проверяем права на запись
        try:
            with open(log_file, 'a') as f:
                pass
        except IOError as e:
            print(f"Error: Unable to write to log file: {e}")
            return

        file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Good Deeds startup')
    except Exception as e:
        print(f"Error setting up logging: {e}")

# Инициализация базы данных с обработкой ошибок
def init_db():
    try:
        with app.app_context():
            db.create_all()
            app.logger.info('Database initialized successfully')
    except Exception as e:
        app.logger.error(f'Error initializing database: {str(e)}')
        raise
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Good Deeds startup')
    
# Improve database error handling
def get_db():
    if 'db' not in g:
        try:
            g.db = db.session
        except Exception as e:
            app.logger.error(f'Database connection error: {str(e)}')
            raise
    return g.db

@app.teardown_appcontext
def teardown_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
