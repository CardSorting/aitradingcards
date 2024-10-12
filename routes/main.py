import os
import base64
import json
import logging
from quart import Blueprint, render_template, jsonify, request, send_from_directory, url_for
from extensions import db
from models import Card
from card_generator import generate_card, generate_card_image, open_pack

# Setup blueprint and logger
main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Utility function to serve images from local storage
@main.route('/card_image/<filename>')
async def card_image(filename):
    image_folder = 'card_images'
    try:
        return await send_from_directory(image_folder, filename)
    except FileNotFoundError:
        logger.error(f"Image file {filename} not found")
        return jsonify({"error": "Image not found"}), 404

# Homepage route - Landing page
@main.route('/')
async def landing_page():
    return await render_template('landing.html')  # Custom landing page template

# Gallery page route - serves as the gallery/collection page
@main.route('/index')
async def index():
    return await render_template('index.html')  # Gallery page

@main.route('/cardbuilder')
async def card_builder():
    return await render_template('card_builder.html')

# Card detail view
@main.route('/card/<int:card_id>')
async def card_detail(card_id):
    card = await Card.query.get_or_404(card_id)

    # Ensure card.image_url uses only the filename
    card.image_url = os.path.basename(card.image_url)
    card.full_image_url = url_for('main.card_image', filename=card.image_url)

    # Prepare card data including all fields used in the template
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

    # Log any missing fields
    for field in card_data:
        if card_data[field] is None:
            logger.warning(f"Card field {field} is not set for card ID {card_id}")

    return await render_template('card_detail.html', card=card_data)

# Route to generate a card and render it on the page
@main.route('/generate_card/<int:card_id>')
async def generate_card_view(card_id):
    card = await Card.query.get_or_404(card_id)

    if not card:
        card_data = generate_card()  # Use your generate_card logic
        card = Card(**card_data)
        card.image_url = generate_card_image(card_data)
        db.session.add(card)
        await db.session.commit()

    # Ensure card image URL uses the correct path
    card.image_url = os.path.basename(card.image_url)
    card.full_image_url = url_for('main.card_image', filename=card.image_url)

    return await render_template('card_detail.html', card=card)

# API route for paginated cards
@main.route('/api/cards')
async def get_cards():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    cards = await Card.query.order_by(Card.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    card_data = [card.to_dict() for card in cards.items]

    return jsonify({
        'cards': card_data,
        'total': cards.total,
        'pages': cards.pages,
        'current_page': page
    })

# API route to generate a single card
@main.route('/api/generate_card', methods=['POST'])
async def api_generate_card():
    try:
        card_data = generate_card()
        cleaned_card_data = clean_card_data(card_data)
        image_filename = generate_card_image(cleaned_card_data)
        cleaned_card_data['image_url'] = image_filename

        new_card = Card(**cleaned_card_data)
        db.session.add(new_card)
        await db.session.commit()

        return jsonify(new_card.to_dict()), 201
    except Exception as e:
        logger.error(f"Error generating card: {str(e)}", exc_info=True)
        await db.session.rollback()
        return jsonify({"error": "Failed to generate card"}), 500

# API route to open a pack of cards
@main.route('/api/open_pack', methods=['POST'])
async def api_open_pack():
    try:
        pack = open_pack()
        card_objects = []

        for card_data in pack:
            cleaned_card_data = clean_card_data(card_data)
            new_card = Card(**clean_card_data)
            db.session.add(new_card)
            card_objects.append(new_card)

        await db.session.commit()
        return jsonify([card.to_dict() for card in card_objects]), 201
    except Exception as e:
        logger.error(f"Error opening pack: {str(e)}", exc_info=True)
        await db.session.rollback()
        return jsonify({"error": "Failed to open pack"}), 500

# Error handlers
@main.errorhandler(404)
async def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@main.errorhandler(500)
async def internal_error(error):
    await db.session.rollback()
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