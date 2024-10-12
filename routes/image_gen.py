import os
import asyncio
import logging
from quart import Blueprint, jsonify, request
from dotenv import load_dotenv
from uuid import uuid4
from models import Card
from extensions import db
from werkzeug.utils import secure_filename
import fal_client

# Load environment variables
load_dotenv()

# Setup blueprint and logger
image_gen = Blueprint('image_gen', __name__)
logger = logging.getLogger(__name__)

# Initialize FalClient with API Key
FAL_KEY = os.getenv('FAL_KEY')
if not FAL_KEY:
    logger.error("FAL_KEY is not set in the environment variables.")
    raise ValueError("FAL_KEY is not set in the environment variables.")

# In-memory storage for tracking image generation requests
image_requests = {}

# Directory to store uploaded images
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@image_gen.route('/api/cards', methods=['POST'])
async def create_card():
    """
    Asynchronous endpoint to create a new card.
    """
    data = await request.get_json()
    required_fields = ['name', 'mana_cost', 'card_type', 'color', 'rarity', 'artist']

    if not data:
        return jsonify({"error": "No data provided."}), 400

    missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}."}), 400

    try:
        new_card = Card(
            name=data['name'].strip(),
            mana_cost=data['mana_cost'].strip(),
            card_type=data['card_type'].strip(),
            color=data['color'].strip(),
            rarity=data['rarity'].strip(),
            artist=data['artist'].strip(),
            abilities=data.get('abilities', '').strip(),
            power_toughness=data.get('power_toughness', '').strip(),
            flavor_text=data.get('flavor_text', '').strip(),
            image_url=data.get('image_url', '').strip()
        )
        db.session.add(new_card)
        await db.session.commit()

        return jsonify({"id": new_card.id, "message": "Card created successfully."}), 201
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        await db.session.rollback()
        return jsonify({"error": "Failed to create card."}), 500


@image_gen.route('/api/image_gen/generate-image', methods=['POST'])
async def generate_image():
    """
    Asynchronous endpoint to submit an image generation request to the FLUX API.
    """
    data = await request.get_json()
    if not data or 'prompt' not in data or 'card_id' not in data:
        return jsonify({"error": "Prompt and card_id are required."}), 400

    prompt = data['prompt']
    card_id = data['card_id']
    image_size = data.get('image_size', 'landscape_4_3')
    num_inference_steps = data.get('num_inference_steps', 28)
    seed = data.get('seed')
    guidance_scale = data.get('guidance_scale', 3.5)
    num_images = data.get('num_images', 1)
    enable_safety_checker = data.get('enable_safety_checker', True)

    # Verify that the Card exists
    card = await Card.query.get(card_id)
    if not card:
        return jsonify({"error": f"Card with id {card_id} does not exist."}), 404

    # Generate a unique request_id
    request_id = str(uuid4())

    async def submit_image_request():
        try:
            # Subscribe to the FLUX API to generate the image
            response = await fal_client.subscribe_async(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": image_size,
                    "num_inference_steps": num_inference_steps,
                    "seed": seed,
                    "guidance_scale": guidance_scale,
                    "num_images": num_images,
                    "enable_safety_checker": enable_safety_checker
                }
            )

            # Extract image URLs from the response
            image_urls = [img['url'] for img in response.get('images', [])]

            # Update the Card instance with AI image details
            if image_urls:
                card.ai_request_id = request_id
                card.ai_image_status = 'COMPLETED'
                card.ai_image_url = image_urls[0]  # Assuming we only use the first image
                await db.session.commit()
                return {"status": "COMPLETED", "image_urls": image_urls}
            else:
                card.ai_image_status = 'FAILED'
                await db.session.commit()
                return {"status": "FAILED", "error": "No image generated."}

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            card.ai_image_status = 'FAILED'
            await db.session.commit()
            return {"status": "FAILED", "error": str(e)}

    # Set the card status to IN_PROGRESS and commit
    card.ai_request_id = request_id
    card.ai_image_status = 'IN_PROGRESS'
    await db.session.commit()

    # Create and run the asyncio task
    task = asyncio.create_task(submit_image_request())
    image_requests[request_id] = task

    # Return the initial request_id, and let the async task complete in the background
    return jsonify({"request_id": request_id, "status": "IN_PROGRESS"}), 202


@image_gen.route('/api/image_gen/request-status/<request_id>', methods=['GET'])
async def request_status(request_id):
    """
    Asynchronous endpoint to check the status of an image generation request.
    Returns the status and image URLs if completed.
    """
    task = image_requests.get(request_id)
    if not task:
        # Check if the request exists in the database
        card = await Card.query.filter_by(ai_request_id=request_id).first()
        if not card:
            return jsonify({"error": "Invalid request_id."}), 404
        else:
            return jsonify({
                "status": card.ai_image_status,
                "image_urls": [card.ai_image_url] if card.ai_image_url else []
            }), 200

    if task.done():
        result = await task
        del image_requests[request_id]  # Remove task from in-memory storage
        return jsonify({
            "status": result['status'],
            "image_urls": result.get('image_urls', []),
            "error": result.get('error', None)
        }), 200
    else:
        return jsonify({"status": "IN_PROGRESS"}), 200