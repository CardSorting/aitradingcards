import os
from quart import Quart
from gino import Gino

# Initialize the Gino database instance
db = Gino()

def create_app():
    app = Quart(__name__)

    # Fetch environment variables from .env file or set default values
    app.config['DB_USER'] = os.getenv('DB_USER', 'yourusername')
    app.config['DB_PASSWORD'] = os.getenv('DB_PASSWORD', 'yourpassword')
    app.config['DB_HOST'] = os.getenv('DB_HOST', 'localhost')
    app.config['DB_PORT'] = os.getenv('DB_PORT', 5432)  # Default Postgres port
    app.config['DB_DATABASE'] = os.getenv('DB_DATABASE', 'yourdatabase')

    # Configure Gino PostgreSQL connection string
    app.config['DB_DSN'] = f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_DATABASE']}"

    # Initialize the Gino database with the Quart app
    db.init_app(app)

    # Import models here to ensure they're known to the database
    from models import Card  # Import your models here

    # Import and register blueprints (routes)
    from routes.main import main as main_blueprint
    from routes.image_gen import image_gen as image_gen_blueprint

    # Register blueprints with unique URL prefixes to prevent route overlaps
    app.register_blueprint(main_blueprint)
    app.register_blueprint(image_gen_blueprint, url_prefix='/api/image_gen')  # Unique prefix

    return app

# Create the Quart application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)