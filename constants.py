# --- Constants for Gambition ---

SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# Map rank string to numerical value (2..14)
CARD_VALUES = {rank: index + 2 for index, rank in enumerate(RANKS)}

# Base damage multipliers for each recognized poker hand
HAND_MULTIPLIERS = {
    'High Card': 0,
    'Pair': 1,
    'Two Pair': 2,
    'Three of a Kind': 3,
    'Straight': 4,
    'Flush': 5,
    'Full House': 9,
    'Four of a Kind': 16,
    'Straight Flush': 25,
    'Royal Flush': 50,
}

# Basic RGB color tuples
WHITE = (255, 255, 255)
BLACK = (0, 0, 0) 