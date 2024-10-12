import os
from datetime import datetime
from gino import Gino

# Initialize the Gino database instance
db = Gino()

class Card(db.Model):
    __tablename__ = 'cards'

    # Define columns using Gino's syntax
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    mana_cost = db.Column(db.String(20), nullable=False)
    card_type = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    abilities = db.Column(db.Text(), nullable=True)
    power_toughness = db.Column(db.String(10), nullable=True)
    flavor_text = db.Column(db.Text(), nullable=True)
    rarity = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # Store only the filename
    set_name = db.Column(db.String(3), nullable=False, default='GEN')
    card_number = db.Column(db.Integer(), nullable=False, default=0)

    # Fields for AI Image Generation
    ai_image_url = db.Column(db.String(255), nullable=True)  # Filename of AI-generated image
    ai_request_id = db.Column(db.String(100), nullable=True, unique=True)  # Unique ID for AI image generation
    ai_image_status = db.Column(db.String(20), nullable=False, default='PENDING')  # Status: PENDING, IN_PROGRESS, COMPLETED, FAILED

    # Timestamp Fields
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('card_number', 'set_name', name='unique_card_in_set'),
    )

    def __init__(self, **kwargs):
        """
        Initialize a new Card instance.
        Ensures that the image_url and ai_image_url are just the filenames without any path.
        """
        image_url = kwargs.get('image_url')
        if image_url and '/' in image_url:
            kwargs['image_url'] = os.path.basename(image_url)

        ai_image_url = kwargs.get('ai_image_url')
        if ai_image_url and '/' in ai_image_url:
            kwargs['ai_image_url'] = os.path.basename(ai_image_url)

        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Card {self.name} (ID: {self.id})>"

    def to_dict(self):
        """
        Convert the Card object to a dictionary.
        Ensures that `image_url` and `ai_image_url` contain only the filenames.
        The frontend will prepend the necessary base URL.
        """
        return {
            'id': self.id,
            'name': self.name,
            'mana_cost': self.mana_cost,
            'card_type': self.card_type,
            'color': self.color,
            'abilities': self.abilities,
            'power_toughness': self.power_toughness,
            'flavor_text': self.flavor_text,
            'rarity': self.rarity,
            'image_url': self.image_url,          # User-uploaded image filename
            'ai_image_url': self.ai_image_url,    # AI-generated image filename
            'ai_request_id': self.ai_request_id,
            'ai_image_status': self.ai_image_status,
            'set_name': self.set_name,
            'card_number': self.card_number,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    async def update_ai_image_status(self, status, ai_image_url=None):
        """
        Update the AI image generation status and optionally set the AI image URL.

        :param status: New status of the AI image generation (e.g., 'COMPLETED').
        :param ai_image_url: (Optional) Filename of the AI-generated image.
        """
        self.ai_image_status = status
        if ai_image_url:
            self.ai_image_url = os.path.basename(ai_image_url)
        await self.update(ai_image_status=self.ai_image_status).apply()