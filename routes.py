from flask import Blueprint, render_template, jsonify, request
from extensions import db
from models import Card
from card_generator import generate_card, generate_card_image, open_pack
from typing import List
import logging

main = Blueprint('main', __name__)

logger = logging.getLogger(__name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/card/<int:card_id>')
def card_detail(card_id):
    card = Card.query.get_or_404(card_id)
    return render_template('card_detail.html', card=card)

@main.route('/api/cards')
def get_cards():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    cards = Card.query.order_by(Card.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    card_data = [card.to_dict() for card in cards.items]

    logger.info(f"Returning {len(card_data)} cards for page {page}")

    return jsonify({
        'cards': card_data,
        'total': cards.total,
        'pages': cards.pages,
        'current_page': page
    })

@main.route('/api/generate_card', methods=['POST'])
def api_generate_card():
    try:
        # Generate the card data using OpenAI
        card_data = generate_card()
        logger.info(f"Generated card data: {card_data}")

        # Clean the card data
        cleaned_card_data = clean_card_data(card_data)
        logger.info(f"Cleaned card data: {cleaned_card_data}")

        # Generate the image URL for the card
        image_url = generate_card_image(cleaned_card_data)
        logger.info(f"Generated image URL: {image_url}")
        cleaned_card_data['image_url'] = image_url

        # Create and store the new card
        new_card = Card(**cleaned_card_data)
        db.session.add(new_card)
        db.session.commit()
        logger.info(f"New card added to database: {new_card.id}")

        return jsonify(new_card.to_dict()), 201
    except Exception as e:
        logger.error(f"Error generating card: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Failed to generate card", "details": str(e)}), 500

@main.route('/api/open_pack', methods=['POST'])
def api_open_pack():
    try:
        pack = open_pack()
        logger.info(f"Generated pack with {len(pack)} cards")
        card_objects = []

        for card_data in pack:
            # Clean the card data
            cleaned_card_data = clean_card_data(card_data)

            new_card = Card(**cleaned_card_data)
            db.session.add(new_card)
            card_objects.append(new_card)

        db.session.commit()
        logger.info(f"Added {len(card_objects)} new cards to database")

        return jsonify([card.to_dict() for card in card_objects]), 201
    except Exception as e:
        logger.error(f"Error opening pack: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Failed to open pack. Please try again later."}), 500

@main.route('/api/clear_database', methods=['POST'])
def clear_database():
    try:
        num_deleted = db.session.query(Card).delete()
        db.session.commit()
        logger.info(f"Cleared database. Deleted {num_deleted} cards.")
        return jsonify({"message": f"Successfully deleted {num_deleted} cards from the database."}), 200
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@main.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

# Utility function to clean card data
def clean_card_data(card_data):
    """Convert OpenAI-generated card data to the proper format expected by the Card model."""
    return {
        'name': card_data.get('name', 'Unnamed Card'),
        'mana_cost': clean_mana_cost(card_data.get('manaCost', '{0}')),
        'card_type': card_data.get('type', 'Unknown Type'),  # Handle card_type properly
        'color': card_data.get('color', 'Colorless'),
        'abilities': ', '.join(card_data.get('abilities', [])),
        'power_toughness': card_data.get('powerToughness', ''),
        'flavor_text': card_data.get('flavorText', 'No flavor text'),
        'rarity': card_data.get('rarity', 'Common'),
        'set_name': card_data.get('set_name', 'GEN'),
        'card_number': card_data.get('card_number', 0),
        'image_url': card_data.get('image_url', None)  # Image URL will be filled in later
    }

def clean_mana_cost(mana_cost: str) -> str:
    """Clean the mana cost string by removing the extra curly braces."""
    return ' '.join(mana_cost.replace('{{', '').replace('}}', '').split())

# Image prompt generation with better handling of the 'type' field
def generate_image_prompt(card_data):
    """Generate an image generation prompt based on card type and attributes."""
    card_type = card_data.get('card_type', 'Unknown')  # Use card_type directly

    prompt = f"Create fantasy artwork for {card_data.get('name', 'Unnamed Card')}. "

    if 'Creature' in card_type:
        prompt += f"Show a {card_type.lower()} in action. "
    elif 'Enchantment' in card_type:
        prompt += "Depict a magical aura or mystical effect. "
    elif 'Artifact' in card_type:
        prompt += "Illustrate a detailed magical item or relic. "
    elif 'Land' in card_type:
        prompt += f"Illustrate a landscape for {card_data.get('name', 'Unnamed Card')}. "
    elif 'Planeswalker' in card_type:
        prompt += f"Show a powerful {card_type.lower()} character. "
    else:
        prompt += "Depict the card's effect in a visually appealing way. "

    prompt += f"Use the {card_data.get('color', 'Colorless')} color scheme with {card_data.get('rarity', 'Common').lower()} quality. "
    prompt += "High detail, dramatic lighting, no text or borders."

    return prompt