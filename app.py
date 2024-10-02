# app.py

import os
import asyncio
from flask import Flask
from flask_migrate import Migrate
from extensions import db
from openai_config import openai_client  # Import OpenAI client from config
from dotenv import load_dotenv  # For loading environment variables

# Load environment variables from .env file (for development)
load_dotenv()

# Import BackblazeHandler
from handlers.backblaze_handler import BackblazeHandler

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

    # Initialize BackblazeHandler
    app.backblaze_handler = initialize_backblaze_handler(app)

    return app

def initialize_backblaze_handler(app: Flask) -> BackblazeHandler:
    """
    Initializes the BackblazeHandler using environment variables and attaches it to the Flask app.
    """
    # Retrieve Backblaze credentials from environment variables
    key_id = os.environ.get('BACKBLAZE_KEY_ID')
    application_key = os.environ.get('BACKBLAZE_APPLICATION_KEY')
    bucket_name = os.environ.get('BACKBLAZE_BUCKET_NAME')
    region_name = os.environ.get('BACKBLAZE_REGION_NAME', 'us-east-005')  # Default region

    if not all([key_id, application_key, bucket_name]):
        raise ValueError("Missing required Backblaze B2 environment variables.")

    # Create an instance of BackblazeHandler
    backblaze_handler = BackblazeHandler(
        key_id=key_id,
        application_key=application_key,
        bucket_name=bucket_name,
        region_name=region_name
    )

    # Initialize the handler asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(backblaze_handler.initialize())
    except Exception as e:
        app.logger.error(f"Failed to initialize BackblazeHandler: {e}")
        raise e
    finally:
        loop.close()

    # Register teardown function to close BackblazeHandler on app shutdown
    @app.teardown_appcontext
    def shutdown_backblaze_handler(exception=None):
        """
        Shuts down the BackblazeHandler when the Flask app context is torn down.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(backblaze_handler.close())
        except Exception as e:
            app.logger.error(f"Error during BackblazeHandler shutdown: {e}")
        finally:
            loop.close()

    app.logger.info("BackblazeHandler initialized and attached to the Flask app.")

    return backblaze_handler

# Create the Flask application instance
app = create_app()

# This context processor makes openai_client available in all templates
@app.context_processor
def inject_openai_client():
    return dict(openai_client=openai_client)

# Only for development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)