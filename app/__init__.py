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

    # Automatically create database tables if they do not exist
    with app.app_context():
        db.create_all()

    return app

# Expose app instance at package level so both `gunicorn app:app` and `gunicorn "app:create_app()"` work
app = create_app()

