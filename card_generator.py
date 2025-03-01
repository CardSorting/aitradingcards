import random
import json
import logging
import os
import requests
from typing import Dict, Any, List, Tuple
from tenacity import retry, stop_after_attempt, wait_random_exponential
from models import Card
from openai_config import openai_client

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
IMAGE_SAVE_PATH = 'card_images'  # Path to save images locally

# Utility functions
def safe_get_dict(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary, providing a default if the key is missing."""
    return data.get(key, default)

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

def standardize_card_data(card_data: Dict[str, Any]) -> None:
    """
    Standardizes the card data field names to lowercase and 
    transfers values from uppercase keys (if they exist).
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

# Card generation logic
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
        f"Create a card with the following attributes:\n"
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

# Image generation logic
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
def generate_card_image(card_data: Dict[str, Any], save_path: str = IMAGE_SAVE_PATH) -> str:
    """Generate fantasy artwork for the card and save the image locally."""
    prompt = generate_image_prompt(card_data)

    try:
        # Generate the image using OpenAI's image API
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url

        # Fetch the image content from the URL
        image_data = requests.get(image_url).content

        # Ensure the save directory exists
        os.makedirs(save_path, exist_ok=True)

        # Generate a unique filename based on card name and number
        file_name = f"{card_data['set_name']}_{card_data['card_number']}.png"
        file_path = os.path.join(save_path, file_name)

        # Save the image to the specified directory
        with open(file_path, 'wb') as image_file:
            image_file.write(image_data)

        logger.info(f"Image saved locally at: {file_path}")
        return file_name  # Return the file name for serving via Flask

    except Exception as e:
        logger.error(f"Error generating or saving card image: {e}")
        raise ValueError(f"Failed to generate or save card image: {e}")

def generate_image_prompt(card_data: Dict[str, Any]) -> str:
    """Generate an image generation prompt based on card type and attributes."""
    card_type = card_data.get('type', 'Unknown')

    prompt = f"Create detailed fantasy artwork for \"{card_data.get('name')}\", which is a {card_type.lower()}. "

    if 'Creature' in card_type:
        prompt += f"Show a {card_type.lower()} in a dynamic scene. "
    elif 'Enchantment' in card_type:
        prompt += "Depict a captivating magical aura or effect. "
    elif 'Artifact' in card_type:
        prompt += "Illustrate an intricate magical item or relic. "
    elif 'Land' in card_type:
        prompt += f"Visualize an evocative landscape called {card_data['name']}. "
    elif 'Planeswalker' in card_type:
        prompt += f"Portray a formidable {card_type.lower()} character. "
    else:
        prompt += "Capture the essence in an intriguing way. "

    prompt += f"Integrate {card_data['color']} hues with elements of {card_data['rarity'].lower()} quality. "
    prompt += "Maintain high detail and dramatic lighting without any text or borders."

    return prompt

# Flexible card generation with optional JSON input
def generate_card_with_rarity(rarity: str, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate a card with the specified rarity, or use the provided JSON data if available.
    """
    try:
        # If JSON data is provided, use it directly
        if json_data:
            card_data = json_data
            standardize_card_data(card_data)  # Standardize field names if necessary
            logger.info(f"Using provided JSON data to generate image for card: {card_data['name']}")
        else:
            # Generate a card if no JSON data is provided
            card_data = generate_card(rarity)

        # Generate the image from the card data
        card_data['image_url'] = generate_card_image(card_data)  # Store the image file name
        return card_data

    except Exception as e:
        logger.error(f"Failed to generate card with rarity {rarity}: {e}")
        raise ValueError(f"Failed to generate card with rarity {rarity}: {e}")

# Pack simulation
def open_pack() -> List[Dict[str, Any]]:
    """Simulate opening a card pack."""
    pack = []

    rarity_probabilities = get_rarity_probabilities()

    # Generate one Rare or Mythic Rare card
    rare_or_mythic = random.choices(['Rare', 'Mythic Rare'], weights=[rarity_probabilities['Rare'], rarity_probabilities['Mythic Rare']])[0]
    pack.append(generate_card_with_rarity(rare_or_mythic))

    # Generate three Uncommon cards
    for _ in range(3):
        pack.append(generate_card_with_rarity('Uncommon'))

    # Generate six Common cards
    for _ in range(6):
        pack.append(generate_card_with_rarity('Common'))

    return pack

def get_rarity_probabilities() -> Dict[str, float]:
    """Fetch or configure the rarity probabilities dynamically."""
    return DEFAULT_RARITY_PROBABILITIES