# card_generator.py

import random
import json
import logging
from typing import Dict, Any, List, Tuple
from tenacity import retry, stop_after_attempt, wait_random_exponential
from models import Card
from openai_config import openai_client
import asyncio
import requests

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SET_NAME = 'GEN'
CARD_NUMBER_LIMIT = 999
DEFAULT_RARITY_PROBABILITIES = {
    'Common': 0.60,
    'Uncommon': 0.30,
    'Rare': 0.08,
    'Mythic Rare': 0.02
}

# Utility functions
def safe_get_dict(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary, providing a default if the key is missing."""
    return data.get(key, default)

def standardize_card_data(card_data: Dict[str, Any]) -> None:
    """
    Standardizes the card data field names to lowercase and transfers values from
    uppercase keys (if they exist).
    Ensures all required fields are present.
    """
    mapping = {
        'Name': 'name',
        'ManaCost': 'manaCost',
        'Type': 'type',
        'Color': 'color',
        'Abilities': 'abilities',
        'FlavorText': 'flavorText',
        'Rarity': 'rarity',
        'PowerToughness': 'powerToughness'
    }

    # Transfer uppercase values to lowercase fields if present
    for old_key, new_key in mapping.items():
        if old_key in card_data:
            card_data[new_key] = card_data.pop(old_key)

    # Validate that all required fields are present and set defaults if missing
    required_fields = ['name', 'manaCost', 'type', 'color', 'abilities', 'flavorText', 'rarity']
    for field in required_fields:
        if field not in card_data or not card_data[field]:
            card_data[field] = get_default_value_for_field(field)

def get_default_value_for_field(field: str) -> Any:
    """Provide default values for missing card fields."""
    default_values = {
        'name': 'Unnamed Card',
        'manaCost': '{0}',
        'type': 'Unknown Type',
        'color': 'Colorless',
        'abilities': 'No abilities',
        'flavorText': 'No flavor text',
        'rarity': 'Common',
        'powerToughness': 'N/A'
    }
    return default_values.get(field, 'Unknown')

# Set and card number handling
def get_next_set_name_and_number() -> Tuple[str, int]:
    """Retrieve the next set name and card number for card generation, reset if needed."""
    last_card = Card.query.order_by(Card.id.desc()).first()

    if not last_card or last_card.card_number >= CARD_NUMBER_LIMIT:
        last_set = last_card.set_name if last_card else DEFAULT_SET_NAME
        next_set = increment_set_name(last_set)
        logger.info(f"New set initialized: {next_set}")
        return next_set, 1

    return last_card.set_name, last_card.card_number + 1

def increment_set_name(set_name: str) -> str:
    """Increment the set name alphabetically (e.g., A -> B, Z -> AA, etc.)."""
    if set_name == 'Z':
        return 'AA'
    if len(set_name) == 1 and set_name < 'Z':
        return chr(ord(set_name) + 1)
    return set_name

# Card generation
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
def generate_card(rarity: str = None) -> Dict[str, Any]:
    """Generate a card with optional rarity, using fallback data on failure."""
    prompt = generate_card_prompt(rarity)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        card_data_str = response.choices[0].message.content
        logger.debug(f"Raw card data from GPT: {card_data_str}")
        card_data = json.loads(card_data_str)

        # Standardize field names and validate card data
        standardize_card_data(card_data)

        # Assign set name and card number
        set_name, card_number = get_next_set_name_and_number()
        card_data['set_name'] = set_name
        card_data['card_number'] = card_number

        return card_data

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error generating card: {e}")
        return generate_fallback_card(rarity)

def generate_card_prompt(rarity: str = None) -> str:
    """Generate the GPT prompt for creating the card."""
    return (
        f"Create a unique Magic: The Gathering card with these attributes:\n"
        "- Name: A creative, thematic name\n"
        "- ManaCost: Using curly braces (e.g., {{2}}{{W}}{{U}})\n"
        "- Type: Full type line (e.g., 'Legendary Creature - Elf Warrior')\n"
        "- Color: White, Blue, Black, Red, Green, or Colorless\n"
        "- Abilities: List of abilities or rules text\n"
        "- PowerToughness: For creatures, e.g., '2/3', or null for non-creatures\n"
        "- FlavorText: A short, thematic description or quote\n"
        f"- Rarity: {rarity if rarity else 'Common, Uncommon, Rare, Mythic Rare'}\n"
        "Return the response as a JSON object."
    )

def generate_fallback_card(rarity: str) -> Dict[str, Any]:
    """Generate a basic fallback card when GPT response is invalid or missing."""
    return {
        'name': 'Default Card',
        'manaCost': '{0}',
        'type': 'Basic Creature - Placeholder',
        'color': 'Colorless',
        'abilities': 'None',
        'flavorText': 'Default fallback card.',
        'rarity': rarity or 'Common',
        'set_name': DEFAULT_SET_NAME,
        'card_number': 1
    }

# Image generation
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
def generate_card_image(card_data: Dict[str, Any], backblaze_handler) -> str:
    """Generate fantasy artwork for the card using OpenAI's image generation API and upload to Backblaze."""
    prompt = generate_image_prompt(card_data)

    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url
        logger.debug(f"Raw image URL from OpenAI: {image_url}")

        # Download the image content
        image_content = download_image(image_url)

        # Define a unique file name, e.g., based on card set and number
        file_name = f"{card_data['set_name']}_{card_data['card_number']}.png"

        # Upload to Backblaze asynchronously
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's an existing event loop, create a new task
            uploaded_url = asyncio.create_task(backblaze_handler.upload_image(file_name, image_content))
            asyncio.run_coroutine_threadsafe(uploaded_url, loop)
            # Wait for the task to complete
            uploaded_url = loop.run_until_complete(uploaded_url)
        else:
            # If no event loop is running, run the coroutine directly
            uploaded_url = loop.run_until_complete(
                backblaze_handler.upload_image(file_name, image_content)
            )

        if not uploaded_url:
            logger.warning(f"Using original image URL due to upload failure: {image_url}")
            return image_url

        return uploaded_url

    except Exception as e:
        logger.error(f"Error generating or uploading card image: {e}")
        # Optionally, return a placeholder image URL or handle as needed
        return generate_fallback_image_url()

def generate_image_prompt(card_data: Dict[str, Any]) -> str:
    """Generate an image generation prompt based on card type and attributes."""
    card_type = card_data.get('type', 'Unknown')

    prompt = f"Create fantasy artwork for {card_data.get('name')}. "

    if 'Creature' in card_type:
        prompt += f"Show a {card_type.lower()} in action. "
    elif 'Enchantment' in card_type:
        prompt += "Depict a magical aura or mystical effect. "
    elif 'Artifact' in card_type:
        prompt += "Illustrate a detailed magical item or relic. "
    elif 'Land' in card_type:
        prompt += f"Illustrate a landscape for {card_data['name']}. "
    elif 'Planeswalker' in card_type:
        prompt += f"Show a powerful {card_type.lower()} character. "
    else:
        prompt += "Depict the card's effect in a visually appealing way. "

    prompt += f"Use the {card_data.get('color', 'Colorless')} color scheme with {card_data.get('rarity', 'Common').lower()} quality. "
    prompt += "High detail, dramatic lighting, no text or borders."

    return prompt

def download_image(image_url: str) -> bytes:
    """Download image content from a URL."""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to download image from '{image_url}': {e}")
        raise e

def generate_fallback_image_url() -> str:
    """Return a fallback image URL in case of failures."""
    return "https://mtginsider.com/wp-content/uploads/2024/06/duskmournart.jpg"  # Replace with an actual fallback URL

# Pack simulation
def open_pack(backblaze_handler) -> List[Dict[str, Any]]:
    """Simulate opening a Magic: The Gathering pack of cards."""
    pack = []

    rarity_probabilities = get_rarity_probabilities()

    # Generate one Rare or Mythic Rare card
    rare_or_mythic = random.choices(['Rare', 'Mythic Rare'], weights=[rarity_probabilities['Rare'], rarity_probabilities['Mythic Rare']])[0]
    pack.append(generate_card_with_rarity(rare_or_mythic, backblaze_handler))

    # Generate three Uncommon cards
    for _ in range(3):
        pack.append(generate_card_with_rarity('Uncommon', backblaze_handler))

    # Generate six Common cards
    for _ in range(6):
        pack.append(generate_card_with_rarity('Common', backblaze_handler))

    return pack

def get_rarity_probabilities() -> Dict[str, float]:
    """Fetch or configure the rarity probabilities dynamically."""
    return DEFAULT_RARITY_PROBABILITIES

def generate_card_with_rarity(rarity: str, backblaze_handler) -> Dict[str, Any]:
    """Generate a card with specified rarity and its corresponding image."""
    try:
        card_data = generate_card(rarity)
        card_data['image_url'] = generate_card_image(card_data, backblaze_handler)
        return card_data
    except Exception as e:
        logger.error(f"Failed to generate card with rarity {rarity}: {e}")
        raise ValueError(f"Failed to generate card with rarity {rarity}: {e}")