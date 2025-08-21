from __future__ import annotations
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
from world_map import WorldMap, DistrictType
from entities.player import Player
import time


class EndingType(Enum):
    """The two possible endings of the game."""
    EMBRACE_DESTINY = "embrace_destiny"
    DEFY_HAND = "defy_hand"


class EndingState(Enum):
    """States of the ending sequence."""
    NOT_STARTED = "not_started"
    VALERIUS_DEFEATED = "valerius_defeated"
    TRUTH_REVEALED = "truth_revealed"
    CHOICE_PRESENTED = "choice_presented"
    CHOICE_MADE = "choice_made"
    ENDING_PLAYING = "ending_playing"
    COMPLETED = "completed"


@dataclass
class EndingConsequence:
    """Consequences of a choice in the final decision."""
    world_changes: List[str]
    player_changes: List[str]
    narrative_changes: List[str]
    post_game_state: Dict[str, Any]


class FinalChoice:
    """Manages the final choice and ending sequence."""
    
    def __init__(self, world_map: WorldMap, player: Player):
        self.world_map = world_map
        self.player = player
        self.current_state = EndingState.NOT_STARTED
        self.chosen_ending: Optional[EndingType] = None
        self.ending_consequences: Dict[EndingType, EndingConsequence] = {}
        
        # Initialize consequences
        self._initialize_consequences()
    
    def _initialize_consequences(self):
        """Initialize the consequences for each ending."""
        
        # Embrace Destiny ending
        embrace_consequences = EndingConsequence(
            world_changes=[
                "Aethelburg is restored to its gilded glory",
                "The Dissonance is completely eradicated",
                "Fortuna flows perfectly throughout the city",
                "The Syndicate maintains control but with benevolent rule",
                "The Ascendancy Engine becomes a source of stability"
            ],
            player_changes=[
                "You become the unseen warden of fate",
                "Your consciousness merges with the Engine",
                "You gain god-like control over probability",
                "You fulfill the purpose your creator set for you",
                "You become immortal but lose your humanity"
            ],
            narrative_changes=[
                "The city becomes a silent, perfect prison",
                "All citizens are subject to your benevolent control",
                "The world outside Aethelburg remains unchanged",
                "You become a legend, whispered in hushed tones",
                "The story of the Homunculus who became a god"
            ],
            post_game_state={
                "player_role": "god_of_fate",
                "city_state": "perfect_prison",
                "freedom_level": 0,
                "control_level": 100,
                "narrative_tone": "benevolent_tyranny"
            }
        )
        self.ending_consequences[EndingType.EMBRACE_DESTINY] = embrace_consequences
        
        # Defy Your Hand ending
        defy_consequences = EndingConsequence(
            world_changes=[
                "The Ascendancy Engine is completely destroyed",
                "All artificial Fortuna is severed forever",
                "Aethelburg loses its magical properties",
                "The city becomes an ordinary metropolis",
                "The Syndicate's power is broken"
            ],
            player_changes=[
                "You reject your manufactured purpose",
                "You become truly human for the first time",
                "You lose your supernatural abilities",
                "You are free to find your own path",
                "You must learn to live as a mortal"
            ],
            narrative_changes=[
                "The people of Aethelburg are truly free",
                "The city becomes subject to real chance and fate",
                "The world outside can now interact with the city",
                "You become a symbol of rebellion and freedom",
                "The story of the Homunculus who chose humanity"
            ],
            post_game_state={
                "player_role": "free_human",
                "city_state": "ordinary_city",
                "freedom_level": 100,
                "control_level": 0,
                "narrative_tone": "liberation"
            }
        )
        self.ending_consequences[EndingType.DEFY_HAND] = defy_consequences
    
    def start_ending_sequence(self) -> bool:
        """Start the ending sequence after Valerius is defeated."""
        if self.current_state != EndingState.NOT_STARTED:
            return False
        
        self.current_state = EndingState.VALERIUS_DEFEATED
        print("\n=== THE FINAL CHOICE ===")
        print("Chairman Valerius lies defeated before the unstable Ascendancy Engine.")
        print("The Engine pulses erratically, threatening to destroy everything.")
        print("You stand at the crossroads of destiny...")
        
        return True
    
    def reveal_truth(self) -> bool:
        """Reveal the truth about the player's origin."""
        if self.current_state != EndingState.VALERIUS_DEFEATED:
            return False
        
        self.current_state = EndingState.TRUTH_REVEALED
        
        print("\n=== THE TRUTH REVEALED ===")
        print("As you approach the Engine, memories flood your mind...")
        print()
        print("You are not human.")
        print("You are a Homunculus - an artificial being crafted from pure Fortuna.")
        print("Your 'mentor' Maestro was the lead alchemist who created you.")
        print("He grew to care for his creation and tried to escape with you.")
        print("Valerius had him captured and disposed of.")
        print()
        print("Your entire journey was orchestrated by Valerius.")
        print("Your 'innate talent' is your very nature.")
        print("Your 'fragmented memories' are the result of incomplete awakening.")
        print("You are not the cure for the Dissonance...")
        print("You are the final, missing component for the Engine.")
        print("You are literally the 'Ace in the Hole' - the perfect catalyst.")
        print()
        print("The Engine pulses, calling to you...")
        
        return True
    
    def present_choice(self) -> bool:
        """Present the final choice to the player."""
        if self.current_state != EndingState.TRUTH_REVEALED:
            return False
        
        self.current_state = EndingState.CHOICE_PRESENTED
        
        print("\n=== THE FINAL DECISION ===")
        print("The unstable Engine threatens to destroy Aethelburg.")
        print("You have two choices:")
        print()
        print("1. EMBRACE DESTINY")
        print("   Step into the Engine and take control.")
        print("   Use your nature as pure Fortuna to stabilize it.")
        print("   Become the unseen warden of fate.")
        print("   Fulfill the ambition your creator set for you.")
        print()
        print("2. DEFY YOUR HAND")
        print("   Reject your manufactured purpose.")
        print("   Overload and destroy the Ascendancy Engine.")
        print("   Sever the flow of artificial Fortuna forever.")
        print("   Walk away as a free person.")
        print()
        print("The choice is yours...")
        
        return True
    
    def make_choice(self, choice: EndingType) -> bool:
        """Make the final choice. Returns True if successful."""
        if self.current_state != EndingState.CHOICE_PRESENTED:
            return False
        
        self.chosen_ending = choice
        self.current_state = EndingState.CHOICE_MADE
        
        print(f"\nYou have chosen: {choice.value.upper()}")
        
        # Apply the consequences
        self._apply_ending_consequences(choice)
        
        return True
    
    def _apply_ending_consequences(self, ending: EndingType):
        """Apply the consequences of the chosen ending."""
        consequences = self.ending_consequences[ending]
        
        print(f"\n=== {ending.value.upper()} ENDING ===")
        
        # Apply world changes
        print("\nWorld Changes:")
        for change in consequences.world_changes:
            print(f"• {change}")
        
        # Apply player changes
        print("\nYour Fate:")
        for change in consequences.player_changes:
            print(f"• {change}")
        
        # Apply narrative changes
        print("\nThe Story:")
        for change in consequences.narrative_changes:
            print(f"• {change}")
        
        # Update game state
        self._update_game_state(consequences.post_game_state)
        
        self.current_state = EndingState.ENDING_PLAYING
    
    def _update_game_state(self, post_game_state: Dict[str, Any]):
        """Update the game state based on the ending."""
        # In a real implementation, this would save the ending state
        # and modify the world accordingly
        
        print(f"\nPost-Game State:")
        for key, value in post_game_state.items():
            print(f"• {key}: {value}")
    
    def play_ending_cutscene(self) -> bool:
        """Play the ending cutscene based on the chosen ending."""
        if self.current_state != EndingState.ENDING_PLAYING:
            return False
        
        if self.chosen_ending == EndingType.EMBRACE_DESTINY:
            self._play_embrace_ending()
        elif self.chosen_ending == EndingType.DEFY_HAND:
            self._play_defy_ending()
        
        self.current_state = EndingState.COMPLETED
        return True
    
    def _play_embrace_ending(self):
        """Play the Embrace Destiny ending cutscene."""
        print("\n=== EMBRACE DESTINY - ENDING CUTSCENE ===")
        print()
        print("You step into the pulsing heart of the Ascendancy Engine.")
        print("Pure Fortuna flows through your artificial veins.")
        print("The Engine recognizes its missing component.")
        print()
        print("As you merge with the machine, you feel your consciousness expand.")
        print("You can see every thread of probability in Aethelburg.")
        print("Every roll of the dice, every spin of the wheel.")
        print("You become the master of chance itself.")
        print()
        print("The Dissonance fades away, replaced by perfect harmony.")
        print("Aethelburg is restored to its gilded glory.")
        print("But it is a silent, perfect prison.")
        print()
        print("You are the unseen warden of fate.")
        print("The Homunculus who became a god.")
        print("The Ace who fulfilled his destiny.")
        print()
        print("The city lives in eternal, beautiful stasis.")
        print("And you watch over it all, from within the Engine.")
        print()
        print("THE END")
    
    def _play_defy_ending(self):
        """Play the Defy Your Hand ending cutscene."""
        print("\n=== DEFY YOUR HAND - ENDING CUTSCENE ===")
        print()
        print("You turn away from the Engine.")
        print("You reject the purpose that was forced upon you.")
        print("You choose to be more than what you were made to be.")
        print()
        print("With a final act of defiance, you overload the Engine.")
        print("The Ascendancy Engine explodes in a cascade of light.")
        print("All artificial Fortuna is severed forever.")
        print()
        print("Aethelburg loses its magical properties.")
        print("The city becomes an ordinary metropolis.")
        print("The people are truly free for the first time.")
        print()
        print("You walk away from the ruins of the Syndicate.")
        print("You are no longer The Ace.")
        print("You are simply a person, free to find your own gamble.")
        print()
        print("The world is subject to the beautiful, terrible randomness of real luck.")
        print("And you are free to face it as a human being.")
        print()
        print("THE END")
    
    def get_ending_summary(self) -> Dict[str, Any]:
        """Get a summary of the chosen ending."""
        if not self.chosen_ending:
            return {}
        
        consequences = self.ending_consequences[self.chosen_ending]
        
        return {
            'ending_type': self.chosen_ending.value,
            'world_changes': consequences.world_changes,
            'player_changes': consequences.player_changes,
            'narrative_changes': consequences.narrative_changes,
            'post_game_state': consequences.post_game_state
        }


class EndingManager:
    """Manages the overall ending system and post-game content."""
    
    def __init__(self, world_map: WorldMap, player: Player):
        self.world_map = world_map
        self.player = player
        self.final_choice: Optional[FinalChoice] = None
        self.ending_completed = False
        self.post_game_content: Dict[str, Any] = {}
    
    def start_final_choice(self) -> FinalChoice:
        """Start the final choice sequence."""
        if self.final_choice:
            return self.final_choice
        
        self.final_choice = FinalChoice(self.world_map, self.player)
        return self.final_choice
    
    def complete_ending(self, ending_type: EndingType) -> bool:
        """Complete an ending and set up post-game content."""
        if not self.final_choice:
            return False
        
        # Make the choice
        if not self.final_choice.make_choice(ending_type):
            return False
        
        # Play the ending cutscene
        if not self.final_choice.play_ending_cutscene():
            return False
        
        # Set up post-game content
        self._setup_post_game_content(ending_type)
        
        self.ending_completed = True
        return True
    
    def _setup_post_game_content(self, ending_type: EndingType):
        """Set up post-game content based on the ending."""
        if ending_type == EndingType.EMBRACE_DESTINY:
            self.post_game_content = {
                'new_game_plus': True,
                'god_mode': True,
                'perfect_control': True,
                'unlock_all_districts': True,
                'infinite_resources': True,
                'narrative': "You have become a god of probability. Start a new game with divine powers."
            }
        else:  # DEFY_HAND
            self.post_game_content = {
                'new_game_plus': True,
                'human_mode': True,
                'true_freedom': True,
                'exploration_enabled': True,
                'real_luck': True,
                'narrative': "You have achieved true freedom. Start a new game as a human being."
            }
    
    def get_post_game_content(self) -> Dict[str, Any]:
        """Get available post-game content."""
        return self.post_game_content.copy()
    
    def start_new_game_plus(self) -> bool:
        """Start a new game plus with modified content."""
        if not self.ending_completed:
            return False
        
        print("\n=== NEW GAME PLUS ===")
        
        if self.final_choice.chosen_ending == EndingType.EMBRACE_DESTINY:
            print("Starting new game with divine powers...")
            print("You retain your god-like abilities.")
            print("All districts are unlocked from the start.")
            print("You have infinite resources.")
        else:
            print("Starting new game as a human being...")
            print("You face true randomness and chance.")
            print("No supernatural abilities.")
            print("Every decision matters more than ever.")
        
        return True


# Example usage and testing
if __name__ == "__main__":
    # Create world map and player
    world_map = WorldMap()
    player = Player()
    
    # Create ending manager
    ending_manager = EndingManager(world_map, player)
    
    # Start final choice
    final_choice = ending_manager.start_final_choice()
    
    # Go through the ending sequence
    final_choice.start_ending_sequence()
    final_choice.reveal_truth()
    final_choice.present_choice()
    
    # Make a choice (simulate player input)
    choice = EndingType.DEFY_HAND  # or EndingType.EMBRACE_DESTINY
    ending_manager.complete_ending(choice)
    
    # Show post-game content
    post_game = ending_manager.get_post_game_content()
    print(f"\nPost-game content: {post_game}")
    
    # Start new game plus
    ending_manager.start_new_game_plus() 