from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.before_first_request
    def before_first_request():
        app.logger.info("Before first request executed.")

    @app.route('/')
    def index():
        return "Hello, World!"

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)