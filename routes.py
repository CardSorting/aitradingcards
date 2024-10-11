import os
import base64
import logging
import requests
from flask import (Blueprint, render_template, jsonify, request,
                   send_from_directory, url_for)
from werkzeug.utils import secure_filename
from extensions import db
from models import Card
from card_generator import generate_card, generate_card_image, open_pack

# Setup blueprint and logger
main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Use environment variables for API credentials
API_USER_ID = os.getenv('HCTI_USER_ID')
API_KEY = os.getenv('HCTI_API_KEY')

# Ensure image directories exist
os.makedirs('card_images', exist_ok=True)
os.makedirs('blob_images', exist_ok=True)


# Serve card images generated via card generator
@main.route('/card_image/<filename>')
def card_image(filename):
    image_folder = 'card_images'
    try:
        return send_from_directory(image_folder, filename)
    except FileNotFoundError:
        logger.error(f"Image file {filename} not found")
        return jsonify({"error": "Image not found"}), 404


# Serve blob images captured via HTML2Canvas
@main.route('/blob_image/<filename>')
def blob_image(filename):
    blob_folder = 'blob_images'
    try:
        return send_from_directory(blob_folder, filename)
    except FileNotFoundError:
        logger.error(f"Blob image file {filename} not found")
        return jsonify({"error": "Blob image not found"}), 404


# Homepage route
@main.route('/')
def index():
    return render_template('index.html')


# Card detail view
@main.route('/card/<int:card_id>')
def card_detail(card_id):
    card = Card.query.get_or_404(card_id)

    # Ensure card.image_url uses only the filename
    card.image_url = os.path.basename(card.image_url)
    card.full_image_url = url_for('main.card_image', filename=card.image_url)

    # Prepare card data for rendering
    card_data = {
        'name': card.name or 'Unnamed Card',
        'mana_cost': card.mana_cost,
        'card_type': card.card_type or 'Unknown Type',
        'color': card.color or 'Colorless',
        'abilities': card.abilities or 'No abilities',
        'flavor_text': card.flavor_text or 'No flavor text',
        'rarity': card.rarity or 'Common',
        'power_toughness': card.power_toughness or 'N/A',
        'set_name': card.set_name or 'GEN',
        'card_number': card.card_number or 0,
        'full_image_url': card.full_image_url
    }

    return render_template('card_detail.html', card=card_data)


# Route to generate image via the HTML/CSS to Image API and save
# Route to generate image via the HTML/CSS to Image API and save
@main.route('/generate_card_image_api', methods=['POST'])
def generate_card_image_api():
    try:
        # Get card ID and fetch card details
        card_id = request.json.get('card_id')
        card = Card.query.get_or_404(card_id)

        # Render HTML for the card (only the card part, no other page content)
        card_html = render_template('card_detail.html', card=card)

        # Send HTML to the HTML/CSS to Image API
        api_url = "https://hcti.io/v1/image"
        auth = (API_USER_ID, API_KEY
                )  # Use secure API credentials from environment variables
        data = {
            'html': card_html,
            'google_fonts': 'Roboto|Open Sans',
            'viewport_width': 375,  # Match the width of your card layout
            'viewport_height': 525  # Match the height of your card layout
        }
        response = requests.post(api_url, json=data, auth=auth)

        if response.status_code == 200:
            # Extract the image URL from the API response
            image_data = response.json()
            image_url = image_data.get('url')

            # Save the image URL back to the card
            card.image_url = image_url
            db.session.commit()

            return jsonify({
                'message': 'Image generated successfully',
                'image_url': image_url
            }), 201

        else:
            logger.error(f"Error generating image from API: {response.text}")
            return jsonify({'error': 'Failed to generate image'}), 500

    except Exception as e:
        logger.error(f"Error generating card image: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to generate card image'}), 500


# API route for paginated cards
@main.route('/api/cards')
def get_cards():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    cards = Card.query.order_by(Card.id.desc()).paginate(page=page,
                                                         per_page=per_page,
                                                         error_out=False)
    card_data = [card.to_dict() for card in cards.items]

    return jsonify({
        'cards': card_data,
        'total': cards.total,
        'pages': cards.pages,
        'current_page': page
    })


# API route to generate a single card via generator and image API
@main.route('/api/generate_card', methods=['POST'])
def api_generate_card():
    try:
        card_data = generate_card()
        cleaned_card_data = clean_card_data(card_data)
        # Generate card image via internal method
        image_filename = generate_card_image(cleaned_card_data)
        cleaned_card_data['image_url'] = image_filename

        # Save the new card
        new_card = Card(**cleaned_card_data)
        db.session.add(new_card)
        db.session.commit()

        # Trigger HTML/CSS to Image API to generate the image and save the URL
        response = requests.post(url_for('main.generate_card_image_api',
                                         _external=True),
                                 json={'card_id': new_card.id})

        if response.status_code == 201:
            return jsonify(new_card.to_dict()), 201
        else:
            logger.error(
                f"Error generating card image from API: {response.text}")
            return jsonify({"error": "Failed to generate card"}), 500

    except Exception as e:
        logger.error(f"Error generating card: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Failed to generate card"}), 500


# API route to open a pack of cards
@main.route('/api/open_pack', methods=['POST'])
def api_open_pack():
    try:
        pack = open_pack()
        card_objects = []

        for card_data in pack:
            cleaned_card_data = clean_card_data(card_data)
            new_card = Card(**cleaned_card_data)
            db.session.add(new_card)
            card_objects.append(new_card)

        db.session.commit()
        return jsonify([card.to_dict() for card in card_objects]), 201
    except Exception as e:
        logger.error(f"Error opening pack: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Failed to open pack"}), 500


# Error handlers
@main.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404


@main.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


# Utility functions
def clean_card_data(card_data):
    return {
        'name': card_data.get('name', 'Unnamed Card'),
        'mana_cost': clean_mana_cost(card_data.get('manaCost', '{0}')),
        'card_type': card_data.get('type', 'Unknown Type'),
        'color': card_data.get('color', 'Colorless'),
        'abilities': ', '.join(card_data.get('abilities', [])),
        'power_toughness': card_data.get('powerToughness', ''),
        'flavor_text': card_data.get('flavorText', 'No flavor text'),
        'rarity': card_data.get('rarity', 'Common'),
        'set_name': card_data.get('set_name', 'GEN'),
        'card_number': card_data.get('card_number', 0),
        'image_url': card_data.get('image_url', None)
    }


def clean_mana_cost(mana_cost: str) -> str:
    return ' '.join(mana_cost.replace('{{', '').replace('}}', '').split())
