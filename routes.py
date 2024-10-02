# routes.py

from flask import Blueprint, render_template, jsonify, request, current_app
from extensions import db
from models import Card
from card_generator import generate_card, open_pack
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
        # Access the BackblazeHandler from the Flask app
        backblaze_handler = current_app.backblaze_handler

        # Generate the card data using the card_generator module
        card_data = generate_card(backblaze_handler)
        logger.info(f"Generated card data: {card_data}")

        # Create and store the new card
        new_card = Card(**card_data)
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
        # Access the BackblazeHandler from the Flask app
        backblaze_handler = current_app.backblaze_handler

        # Open a pack using the card_generator module
        pack = open_pack(backblaze_handler)
        logger.info(f"Generated pack with {len(pack)} cards")

        # Create and store all new cards in the database
        card_objects = []
        for card_data in pack:
            new_card = Card(**card_data)
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