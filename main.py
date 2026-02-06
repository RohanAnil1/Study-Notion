from flask import Flask
from extensions import db, login_manager, migrate
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
from models import User
import filters

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Initialize custom filters
    filters.init_app(app)

    # Setup user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Configure login view
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Setup logging only if not running migrations
    if not app.debug and not app.testing and not os.environ.get('FLASK_DB_COMMAND'):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'websiteenhancer.log'),
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('WebsiteEnhancer startup')

    # Import and register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    # Create tables and seed initial data
    with app.app_context():
        # Ensure database directory exists (works for any absolute SQLite path)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '', 1)
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        db.create_all()
        from models import load_initial_data
        load_initial_data()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)