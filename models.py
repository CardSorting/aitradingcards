from extensions import db

class Card(db.Model):
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    mana_cost = db.Column(db.String(20), nullable=False)
    card_type = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    abilities = db.Column(db.Text, nullable=True)
    power_toughness = db.Column(db.String(10), nullable=True)
    flavor_text = db.Column(db.Text, nullable=True)
    rarity = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # Store only the filename
    set_name = db.Column(db.String(3), nullable=False, default='GEN')
    card_number = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint('card_number', 'set_name', name='unique_card_in_set'),
    )

    def __init__(self, **kwargs):
        """
        Initialize a new Card instance.
        Ensures that the image_url is just the filename without any path.
        """
        # If image_url contains any path components, extract only the filename
        image_url = kwargs.get('image_url')
        if image_url and '/' in image_url:
            kwargs['image_url'] = os.path.basename(image_url)
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Card {self.name} (ID: {self.id})>"

    def to_dict(self):
        """
        Convert the Card object to a dictionary.
        Ensures that `image_url` contains only the filename.
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
            'image_url': self.image_url,  # Return only the filename
            'set_name': self.set_name,
            'card_number': self.card_number
        }