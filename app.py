import os
from flask import Flask
from flask_migrate import Migrate
from extensions import db
from openai_config import openai_client  # Import OpenAI client from config

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)

    # Set SQLite database URI for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # SQLite file-based DB

    # Disable SQLAlchemy event notifications
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Import models here to ensure they're known to Flask-Migrate
    from models import Card  # Make sure to import all your models

    # Import and register blueprints (routes)
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

# Create the Flask application instance
app = create_app()

# This context processor makes openai_client available in all templates
@app.context_processor
def inject_openai_client():
    return dict(openai_client=openai_client)

# Only for development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)