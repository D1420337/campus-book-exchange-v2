import os
from flask import Flask, render_template
from app.models import db
from app.routes import auth_bp, books_bp, cabinet_bp, requests_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-12345'
    
    # Configure SQLite database path under instance/
    database_path = os.path.join(app.instance_path, 'database.db')
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db
    db.init_app(app)

    # Configure SQLite to use WAL mode and busy_timeout to avoid database locking/exclusive lock issues
    with app.app_context():
        from sqlalchemy import event
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(cabinet_bp)
    app.register_blueprint(requests_bp)

    @app.route('/')
    def index():
        from app.models.book import Book
        # Fetch latest available books for landing page
        try:
            recent_books = Book.query.filter_by(status='Available').order_by(Book.created_at.desc()).limit(8).all()
        except Exception:
            recent_books = []
        return render_template('index.html', recent_books=recent_books)

    @app.route('/dashboard')
    def dashboard_redirect():
        from flask import redirect, url_for
        return redirect(url_for('cabinet.index'))

    # Automatically create database tables if they do not exist, and seed initial data if empty
    with app.app_context():
        db.create_all()
        seed_initial_data()

    return app

def seed_initial_data():
    from app.models.user import User
    from app.models.book import Book

    # If users table is empty, seed demo accounts
    if User.query.count() == 0:
        demo_user = User(
            email='d1420337@o365.fcu.edu.tw',
            username='小明',
            contact_info='Line ID: fcu_book_demo',
            is_verified=True,
            password_hash='scrypt:32768:8:1$Oktb2fmVywgsF04z$67cbf996224a26d393b5b0887104bbccc2c80019468d92d6a2f040ba4993e163ea04afce8a5c8cb59e74a431a86839f020ef0346e14716a1a78d798cf1308aa3'
        )
        buyer_user = User(
            email='test1@o365.fcu.edu.tw',
            username='張同學',
            contact_info='0912345678',
            is_verified=True,
            password_hash='scrypt:32768:8:1$IlKx6XgYyPjJYKdm$03619a49da04784f399e8bd1475606e4da75b0b268ba41f763b73545eb62d623c63a7c5a6292c535250571e81e65d27de13de65934d741dfbf2eb1b7d97a2147'
        )
        db.session.add(demo_user)
        db.session.add(buyer_user)
        db.session.commit()

    # If books table is empty, seed sample books
    if Book.query.count() == 0:
        seller = User.query.filter_by(email='d1420337@o365.fcu.edu.tw').first()
        if seller:
            book1 = Book(
                seller_id=seller.id,
                title='我是誰?一本小書也是一本大書',
                author='逢甲大學國語文教學中心',
                publisher='五南圖書出版公司',
                isbn='978-626-393-666-9(836)',
                price=150,
                is_exchange=False,
                exchange_item='',
                condition='接近全新',
                description='無劃記，書況良好。',
                image_url='/static/uploads/1780927288_0_13502.jpg,/static/uploads/1780927288_1_13504.jpg,/static/uploads/1780927288_2_13503.jpg',
                status='Available',
                dept='各學系',
                subject='中文思辨與表達',
                publish_year='2024',
                edition='修訂一版'
            )
            book2 = Book(
                seller_id=seller.id,
                title='管理學概論',
                author='李慶芳、陳可杰、蔡敦浩',
                publisher='滄海書局',
                isbn='978-626-97291-5-9',
                price=250,
                is_exchange=False,
                exchange_item='',
                condition='輕微劃記',
                description='有用鉛筆畫記過，書況尚好。',
                image_url='/static/uploads/1780927674_0_13501.jpg',
                status='Available',
                dept='經濟學系',
                subject='管理學',
                publish_year='2023',
                edition='第二版'
            )
            db.session.add(book1)
            db.session.add(book2)
            db.session.commit()


# Expose app instance at package level so both `gunicorn app:app` and `gunicorn "app:create_app()"` work
app = create_app()

