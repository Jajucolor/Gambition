from __future__ import annotations
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
from world_map import WorldMap, DistrictType
from quest_system import QuestManager, Quest


class DialogueType(Enum):
    """Types of dialogue responses."""
    GREETING = "greeting"
    QUEST_OFFER = "quest_offer"
    QUEST_UPDATE = "quest_update"
    QUEST_COMPLETE = "quest_complete"
    LORE = "lore"
    TRADE = "trade"
    GOODBYE = "goodbye"


class NPCType(Enum):
    """Types of NPCs in the game."""
    MERCHANT = "merchant"
    QUEST_GIVER = "quest_giver"
    COMPANION = "companion"
    STORY_NPC = "story_npc"
    BOSS = "boss"
    HOSTILE = "hostile"


@dataclass
class DialogueChoice:
    """A single dialogue choice option."""
    text: str
    next_dialogue: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None
    quest_trigger: Optional[str] = None


@dataclass
class DialogueNode:
    """A single node in a dialogue tree."""
    id: str
    text: str
    choices: List[DialogueChoice]
    npc_emotion: str = "neutral"
    background_music: Optional[str] = None


class NPC:
    """Represents a non-player character in the game."""
    
    def __init__(self,
                 npc_id: str,
                 name: str,
                 npc_type: NPCType,
                 district: DistrictType,
                 position: tuple,
                 dialogue_tree: Dict[str, DialogueNode],
                 quest_giver: bool = False,
                 merchant: bool = False,
                 on_interact: Optional[Callable] = None):
        
        self.npc_id = npc_id
        self.name = name
        self.npc_type = npc_type
        self.district = district
        self.position = position
        self.dialogue_tree = dialogue_tree
        self.quest_giver = quest_giver
        self.merchant = merchant
        self.on_interact = on_interact
        
        # NPC state
        self.met_player: bool = False
        self.relationship_level: int = 0  # -2 to +2
        self.quests_given: List[str] = []
        self.quests_completed: List[str] = []
        
        # Current dialogue state
        self.current_dialogue: Optional[str] = None
        self.dialogue_history: List[str] = []
    
    def get_greeting_dialogue(self) -> str:
        """Get appropriate greeting based on relationship and history."""
        if not self.met_player:
            return "greeting_first_time"
        elif self.relationship_level >= 1:
            return "greeting_friendly"
        elif self.relationship_level <= -1:
            return "greeting_hostile"
        else:
            return "greeting_neutral"
    
    def can_give_quest(self, quest_id: str) -> bool:
        """Check if this NPC can give a specific quest."""
        return self.quest_giver and quest_id not in self.quests_given
    
    def has_completed_quest(self, quest_id: str) -> bool:
        """Check if this NPC has had a quest completed for them."""
        return quest_id in self.quests_completed
    
    def update_relationship(self, change: int):
        """Update relationship level with the player."""
        self.relationship_level = max(-2, min(2, self.relationship_level + change))
    
    def mark_quest_given(self, quest_id: str):
        """Mark that this NPC has given a quest."""
        if quest_id not in self.quests_given:
            self.quests_given.append(quest_id)
    
    def mark_quest_completed(self, quest_id: str):
        """Mark that a quest has been completed for this NPC."""
        if quest_id not in self.quests_completed:
            self.quests_completed.append(quest_id)
            self.update_relationship(1)  # Positive relationship change
    
    def get_current_dialogue(self) -> Optional[DialogueNode]:
        """Get the current dialogue node for this NPC."""
        if not self.current_dialogue:
            # Start with greeting if no current dialogue
            greeting_id = self.get_greeting_dialogue()
            if greeting_id in self.dialogue_tree:
                self.current_dialogue = self.dialogue_tree[greeting_id]
            else:
                # Fallback: return the first available dialogue
                first_key = next(iter(self.dialogue_tree), None)
                if first_key:
                    self.current_dialogue = self.dialogue_tree[first_key]
        
        return self.current_dialogue
    
    def process_choice(self, choice_index: int, player_stats) -> str:
        """Process a dialogue choice and return the result."""
        current = self.get_current_dialogue()
        if not current or choice_index >= len(current.choices):
            return 'INVALID'
        
        choice = current.choices[choice_index]
        
        # Execute choice action if present
        if choice.action:
            choice.action(player_stats)  # Pass player_stats to the action
        
        # Check conditions
        if choice.condition and not choice.condition():
            return 'INVALID'
        
        # Move to next dialogue
        if choice.next_dialogue in self.dialogue_tree:
            self.current_dialogue = self.dialogue_tree[choice.next_dialogue]
            self.dialogue_history.append(choice.next_dialogue)
            
            # Check for special dialogue nodes
            if choice.next_dialogue == "combat_start":
                return 'combat_triggered'
            
            return 'CONTINUE'
        
        # End dialogue
        self.current_dialogue = None
        return 'END'
    
    def reset_dialogue(self):
        """Reset the dialogue to the beginning."""
        self.current_dialogue = None
        self.dialogue_history = []


class DialogueManager:
    """Manages dialogue interactions and branching conversations."""
    
    def __init__(self, quest_manager: QuestManager, world_map: WorldMap):
        self.quest_manager = quest_manager
        self.world_map = world_map
        self.npcs: Dict[str, NPC] = {}
        self.current_dialogue: Optional[DialogueNode] = None
        self.dialogue_history: List[str] = []
        
        # Initialize all NPCs
        self._initialize_npcs()
    
    def _valerius_interaction(self):
        """Handle special interactions with Chairman Valerius."""
        # Check if player has completed arrival quest
        if "arrival" in self.quest_manager.completed_quests:
            # Player has completed arrival, show next quest dialogue
            valerius = self.npcs["chairman_valerius"]
            valerius.current_dialogue = "quest_complete_arrival"
        
        # Check if player should receive deck
        if any(q.quest_id == "arrival" for q in self.quest_manager.get_active_quests()):
            # Mark receive_deck objective as complete when talking to Valerius
            self.quest_manager.update_quest_progress("arrival", "receive_deck", 1)
            # Also mark meet_valerius objective
            self.quest_manager.update_quest_progress("arrival", "meet_valerius", 1)
    
    def _intruder_interaction(self):
        """Handle special interactions with the Suspicious Intruder."""
        # This NPC becomes hostile and starts combat when certain dialogue choices are made
        pass
    
    def _merchant_interaction(self):
        """Handle special interactions with the Wandering Merchant."""
        # This could handle actual item purchases in the future
        pass
    
    def _initialize_npcs(self):
        """Initialize all NPCs in the game."""
        
        # Chairman Valerius - Main story NPC and quest giver
        valerius_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "Ah, you must be the one they call 'The Ace.' I am Chairman Valerius, leader of the Syndicate of Providence. Welcome to Aethelburg, though I fear you've arrived at a troubled time. I see you've already proven your combat skills against that intruder. Take this companion - The Joker. It will aid you in your battles.",
                [
                    DialogueChoice("Tell me about the Dissonance", "explain_dissonance"),
                    DialogueChoice("What is the Syndicate?", "explain_syndicate"),
                    DialogueChoice("What do you need me to do?", "quest_offer"),
                    DialogueChoice("Check my current objectives", "quest_status")
                ],
                npc_emotion="concerned"
            ),
            "explain_dissonance": DialogueNode(
                "explain_dissonance",
                "The Dissonance is a corruption of our city's lifeblood - Fortuna. It twists the minds and bodies of those exposed to it, turning them into the Twisted you've already encountered. We believe there's a central source, a 'Heart of Chaos' that must be purified.",
                [
                    DialogueChoice("How can I help?", "offer_help"),
                    DialogueChoice("What caused this?", "dissonance_cause"),
                    DialogueChoice("Tell me about Fortuna", "explain_fortuna")
                ],
                npc_emotion="serious"
            ),
            "explain_syndicate": DialogueNode(
                "explain_syndicate",
                "The Syndicate of Providence has governed Aethelburg for decades, maintaining the balance of luck and order. We control the flow of Fortuna through the city's districts, ensuring prosperity for all. But now... something has gone terribly wrong.",
                [
                    DialogueChoice("How can I help?", "offer_help"),
                    DialogueChoice("What went wrong?", "dissonance_cause")
                ],
                npc_emotion="proud"
            ),
            "mentor_inquiry": DialogueNode(
                "mentor_inquiry",
                "Your mentor... you mean the Maestro? He was investigating the source of the Dissonance before he disappeared. I fear he may have gotten too close to the truth. But first, you must prove yourself capable.",
                [
                    DialogueChoice("How can I prove myself?", "offer_help"),
                    DialogueChoice("What happened to him?", "maestro_fate")
                ],
                npc_emotion="grave"
            ),
            "maestro_fate": DialogueNode(
                "maestro_fate",
                "The Maestro was last seen heading toward the Casino District. That area has been... problematic lately. The corruption there runs deep. If you can cleanse it, you might find clues about his fate.",
                [
                    DialogueChoice("I'll investigate the Casino District", "accept_quest"),
                    DialogueChoice("I need more information first", "explain_dissonance")
                ],
                npc_emotion="concerned"
            ),
            "offer_help": DialogueNode(
                "offer_help",
                "Your arrival is most fortuitous. I sense in you a unique ability to manipulate Fortuna through your cards. I would ask you to investigate the Dissonance and help us find its source. In return, I can provide resources and access to our facilities.",
                [
                    DialogueChoice("I accept your offer", "accept_quest"),
                    DialogueChoice("I need to think about it", "consider_offer"),
                    DialogueChoice("What resources can you provide?", "explain_resources")
                ],
                npc_emotion="hopeful"
            ),
            "accept_quest": DialogueNode(
                "accept_quest",
                "Excellent! Take this Syndicate Standard deck - it will serve you well in your battles against the Twisted. Start by clearing the corrupted guards from the Grand Terminal, then seek me out again for your next assignment.",
                [
                    DialogueChoice("I understand. I'll get started", "quest_accepted"),
                    DialogueChoice("Tell me more about the deck", "explain_deck")
                ],
                npc_emotion="determined"
            ),
            "quest_accepted": DialogueNode(
                "quest_accepted",
                "Good luck, Ace. The fate of Aethelburg may rest in your hands.",
                [],
                npc_emotion="serious"
            ),
            "explain_deck": DialogueNode(
                "explain_deck",
                "The Syndicate Standard is a balanced deck designed for versatility. It contains reliable poker hands and a few special cards infused with Fortuna. Use it wisely - your life may depend on it.",
                [
                    DialogueChoice("Thank you. I'll get started", "quest_accepted")
                ],
                npc_emotion="instructive"
            ),
            "consider_offer": DialogueNode(
                "consider_offer",
                "I understand your hesitation, but time is not on our side. The Dissonance spreads with each passing hour. Return to me when you're ready to help save this city.",
                [],
                npc_emotion="patient"
            ),
            "explain_resources": DialogueNode(
                "explain_resources",
                "The Syndicate controls the Guild of Cartomancers, where you can upgrade your abilities, and the Grand Market, where you can purchase supplies. We also have safe houses throughout the city for rest and planning.",
                [
                    DialogueChoice("That sounds helpful. I accept", "accept_quest"),
                    DialogueChoice("I need to think about it", "consider_offer")
                ],
                npc_emotion="explanatory"
            ),
            "dissonance_cause": DialogueNode(
                "dissonance_cause",
                "We believe someone or something is deliberately corrupting the Fortuna conduits. The pattern is too organized to be natural. There are whispers of a rogue faction, but we need proof.",
                [
                    DialogueChoice("I'll help you find proof", "accept_quest"),
                    DialogueChoice("Tell me about these whispers", "explain_rogue_faction")
                ],
                npc_emotion="suspicious"
            ),
            "explain_rogue_faction": DialogueNode(
                "explain_rogue_faction",
                "Some call them the 'Chaos Dealers' - former Syndicate members who believe order itself is the enemy. They seek to unleash pure, uncontrolled luck upon the world. Madness, if you ask me.",
                [
                    DialogueChoice("I'll stop them", "accept_quest"),
                    DialogueChoice("How can I identify them?", "identify_rogues")
                ],
                npc_emotion="disdainful"
            ),
            "identify_rogues": DialogueNode(
                "identify_rogues",
                "They mark themselves with inverted Syndicate symbols and speak in riddles about 'embracing chaos.' But be careful - they're dangerous and unpredictable. Some have been twisted by their own experiments.",
                [
                    DialogueChoice("I'll be careful. Let me help", "accept_quest")
                ],
                npc_emotion="warning"
            ),
            "explain_fortuna": DialogueNode(
                "explain_fortuna",
                "Fortuna is the essence of probability itself - crystallized luck that flows through our city like blood through veins. We harvest it from chance events and channel it to maintain balance. But now it's being corrupted into something... wrong.",
                [
                    DialogueChoice("How can I help restore it?", "accept_quest"),
                    DialogueChoice("What happens if it stays corrupted?", "corruption_consequences")
                ],
                npc_emotion="scholarly"
            ),
            "corruption_consequences": DialogueNode(
                "corruption_consequences",
                "If the corruption spreads, reality itself will become unstable. Impossible events will become commonplace. People will transform into creatures of pure chaos. Aethelburg will become a nightmare realm where nothing makes sense.",
                [
                    DialogueChoice("I won't let that happen", "accept_quest")
                ],
                npc_emotion="grave"
            ),
            # Quest completion dialogues
            "quest_complete_arrival": DialogueNode(
                "quest_complete_arrival",
                "Excellent work clearing the Terminal! I can see you're as capable as the legends suggest. Now, I have a more challenging task for you - investigate the Casino District. The corruption there runs deep.",
                [
                    DialogueChoice("Tell me about the Casino District", "explain_casino"),
                    DialogueChoice("I'm ready for the next mission", "start_casino_quest")
                ],
                npc_emotion="pleased"
            ),
            "explain_casino": DialogueNode(
                "explain_casino",
                "The Casino District was once the heart of Aethelburg's prosperity. Now it's become a den of corrupted gambling and twisted luck. The manager there has been... changed by the Dissonance. You'll need to confront him directly.",
                [
                    DialogueChoice("I understand. I'll investigate", "start_casino_quest")
                ],
                npc_emotion="serious"
            ),
            "start_casino_quest": DialogueNode(
                "start_casino_quest",
                "Be extremely careful in there. The very air is thick with corrupted Fortuna. Trust your instincts, and remember - the house always wins, unless you change the rules of the game.",
                [],
                npc_emotion="concerned"
            ),
            "quest_status": DialogueNode(
                "quest_status",
                "Let me check your current objectives...",
                [
                    DialogueChoice("What should I do next?", "quest_hint"),
                    DialogueChoice("I'm ready for new assignments", "offer_help"),
                    DialogueChoice("That's all for now", "goodbye")
                ],
                npc_emotion="helpful"
            ),
            "quest_hint": DialogueNode(
                "quest_hint",
                "Your current objective: Clear the Grand Terminal of 3 Twisted guards, then return to me for your next assignment.",
                [
                    DialogueChoice("Understood", "goodbye"),
                    DialogueChoice("Any tips for fighting them?", "explain_deck")
                ],
                npc_emotion="instructive"
            ),
            "goodbye": DialogueNode(
                "goodbye",
                "May Fortuna guide your path, Ace. Return to me when you have news.",
                [],
                npc_emotion="formal"
            )
        }
        
        # Create Chairman Valerius NPC
        valerius = NPC(
            npc_id="chairman_valerius",
            name="Chairman Valerius",
            npc_type=NPCType.QUEST_GIVER,
            district=DistrictType.GRAND_TERMINAL,
            position=(0, 0.5, -50),
            dialogue_tree=valerius_dialogue,
            quest_giver=True,
            on_interact=self._valerius_interaction
        )
        self.npcs["chairman_valerius"] = valerius
        
        # The Cartomancer - Tarot merchant and lore keeper
        cartomancer_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "Ah, a new face in my humble shop. I am the Cartomancer, keeper of the ancient Tarot arts. I sense you have a connection to the cards, do you not?",
                [
                    DialogueChoice("Tell me about Tarot cards", "explain_tarot"),
                    DialogueChoice("What do you sell?", "show_inventory"),
                    DialogueChoice("How do you know about my connection?", "sense_ability")
                ],
                npc_emotion="mysterious"
            ),
            "explain_tarot": DialogueNode(
                "explain_tarot",
                "Tarot cards are vessels of pure Fortuna, crystallized into physical form. Each card holds a fragment of destiny, waiting to be unleashed. In Aethelburg, they are more than mere fortune-telling tools - they are weapons of fate itself.",
                [
                    DialogueChoice("How do they work in combat?", "tarot_combat"),
                    DialogueChoice("Where do they come from?", "tarot_origin"),
                    DialogueChoice("Show me your wares", "show_inventory")
                ],
                npc_emotion="scholarly"
            ),
            "show_inventory": DialogueNode(
                "show_inventory",
                "I have several Tarot cards available for purchase. Each has unique properties that can enhance your abilities in combat. The Sun brings light and healing, the Moon offers protection, and the Tower... well, the Tower is special.",
                [
                    DialogueChoice("I'll buy The Sun", "purchase_sun"),
                    DialogueChoice("I'll buy The Moon", "purchase_moon"),
                    DialogueChoice("Tell me about The Tower", "tower_lore")
                ],
                npc_emotion="businesslike"
            )
        }
        
        cartomancer = NPC(
            npc_id="cartomancer",
            name="The Cartomancer",
            npc_type=NPCType.MERCHANT,
            district=DistrictType.GILDED_PROMENADE,
            position=(20, 1, 10),
            dialogue_tree=cartomancer_dialogue,
            merchant=True,
            on_interact=lambda: self._on_cartomancer_interact()
        )
        self.npcs["cartomancer"] = cartomancer
        
        # Press Foreman - Twisted boss with tragic backstory
        foreman_dialogue = {
            "greeting_boss": DialogueNode(
                "greeting_boss",
                "Grrr... another Syndicate puppet come to 'clean up' the mess? I was once a proud foreman, until Valerius promised me wealth beyond imagination. Look what his 'Ascendancy Engine' did to me!",
                [
                    DialogueChoice("Tell me about the Ascendancy Engine", "engine_truth"),
                    DialogueChoice("What happened to you?", "personal_tragedy"),
                    DialogueChoice("I'm not here for the Syndicate", "clarify_motive")
                ],
                npc_emotion="angry"
            ),
            "engine_truth": DialogueNode(
                "engine_truth",
                "The Ascendancy Engine... it was supposed to concentrate Fortuna, make us all rich. But it's malfunctioning, leaking corrupted energy. Valerius doesn't want to fix it - he wants to control it! He's using the Dissonance to test his subjects!",
                [
                    DialogueChoice("How do you know this?", "source_knowledge"),
                    DialogueChoice("Where is the Engine?", "engine_location"),
                    DialogueChoice("I believe you", "accept_truth")
                ],
                npc_emotion="desperate"
            )
        }
        
        foreman = NPC(
            npc_id="press_foreman",
            name="Twisted Press Foreman",
            npc_type=NPCType.BOSS,
            district=DistrictType.PRINTING_PRESS_QUARTER,
            position=(0, 1, 0),
            dialogue_tree=foreman_dialogue,
            on_interact=lambda: self._on_foreman_interact()
        )
        self.npcs["press_foreman"] = foreman
        
        # Underdeck Guardian - Joker recruiter
        guardian_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "Well, well... a fresh face in The Underdeck. I'm the Guardian, keeper of this hidden realm. You're not Syndicate, are you? Good. We don't take kindly to their kind down here.",
                [
                    DialogueChoice("Tell me about The Underdeck", "explain_underdeck"),
                    DialogueChoice("I'm looking for Jokers", "joker_info"),
                    DialogueChoice("What do you guard?", "guardian_purpose")
                ],
                npc_emotion="suspicious"
            ),
            "joker_info": DialogueNode(
                "joker_info",
                "Jokers? Ah, you mean the free spirits who've found ways to thrive in this chaos. We have several here - the Fortune Teller who reads probability, the Berserker who grows stronger with time, and the Echo Mage who can duplicate cards. They're not for sale, but they might join your cause if you prove yourself worthy.",
                [
                    DialogueChoice("How do I prove myself?", "prove_worthiness"),
                    DialogueChoice("Tell me about each Joker", "joker_details"),
                    DialogueChoice("I'm ready to fight", "guardian_challenge")
                ],
                npc_emotion="assessing"
            )
        }
        
        guardian = NPC(
            npc_id="underdeck_guardian",
            name="Underdeck Guardian",
            npc_type=NPCType.QUEST_GIVER,
            district=DistrictType.THE_UNDERDECK,
            position=(0, -5, 0),
            dialogue_tree=guardian_dialogue,
            quest_giver=True,
            on_interact=lambda: self._on_guardian_interact()
        )
        self.npcs["underdeck_guardian"] = guardian

        # Beggar NPC (mysterious ???)
        beggar_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "??? : could you spare some money?",
                [
                                    DialogueChoice("Invite to the team", "invited"),
                DialogueChoice("Give money", "gave_money"),
                    DialogueChoice("Ignore", "goodbye"),
                ],
            ),
            "invited": DialogueNode(
                "invited",
                "...",
                [DialogueChoice("Goodbye", "goodbye")],
            ),
            "gave_money": DialogueNode(
                "gave_money",
                "Thank you...",
                [DialogueChoice("Goodbye", "goodbye")],
            ),
            "goodbye": DialogueNode("goodbye", "...", []),
        }

        beggar = NPC(
            npc_id="beggar_mystery",
            name="???",
            npc_type=NPCType.COMPANION,
            district=DistrictType.GRAND_TERMINAL,
            position=(10, 0.5, 10),
            dialogue_tree=beggar_dialogue,
            on_interact=lambda: None,
        )
        self.npcs["beggar_mystery"] = beggar
        
        # Add the basic NPCs that were previously created separately
        # Quest Giver (Village Elder)
        quest_giver_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "Welcome, traveler. I have a quest for you.",
                [
                    DialogueChoice("Tell me about the quest", "quest_details"),
                    DialogueChoice("Goodbye", "goodbye")
                ]
            ),
            "quest_details": DialogueNode(
                "quest_details",
                "Defeat the enemies in the area and return to me.",
                [
                    DialogueChoice("I accept", "quest_accepted"),
                    DialogueChoice("Maybe later", "goodbye")
                ]
            ),
            "quest_accepted": DialogueNode(
                "quest_accepted",
                "Excellent! Return when you have completed the task.",
                [
                    DialogueChoice("Goodbye", "goodbye")
                ]
            ),
            "goodbye": DialogueNode(
                "goodbye",
                "Farewell, brave adventurer.",
                []
            )
        }
        
        quest_giver = NPC(
            npc_id="quest_giver",
            name="Village Elder",
            npc_type=NPCType.QUEST_GIVER,
            district=DistrictType.GRAND_TERMINAL,
            position=(-15, 0.5, 5),
            dialogue_tree=quest_giver_dialogue,
            quest_giver=True,
            on_interact=lambda: print("Quest giver interaction")
        )
        self.npcs["quest_giver"] = quest_giver
        
        # Wandering Merchant
        merchant_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "Welcome to my humble shop! What can I interest you in today?",
                [
                    DialogueChoice("Show me your wares", "show_wares"),
                    DialogueChoice("Goodbye", "goodbye")
                ]
            ),
            "greeting_neutral": DialogueNode(
                "greeting_neutral",
                "Ah, welcome back! Looking for something specific today?",
                [
                    DialogueChoice("Show me your wares", "show_wares"),
                    DialogueChoice("Goodbye", "goodbye")
                ]
            ),
            "greeting_friendly": DialogueNode(
                "greeting_friendly",
                "My favorite customer! What can I help you with today?",
                [
                    DialogueChoice("Show me your wares", "show_wares"),
                    DialogueChoice("Goodbye", "goodbye")
                ]
            ),
            "greeting_hostile": DialogueNode(
                "greeting_hostile",
                "What do you want? I'm busy.",
                [
                    DialogueChoice("Show me your wares", "show_wares"),
                    DialogueChoice("Goodbye", "goodbye")
                ]
            ),
            "show_wares": DialogueNode(
                "show_wares",
                "Here's what I have in stock today:",
                [
                    DialogueChoice("Healing Potion (50 gold)", "buy_healing_potion"),
                    DialogueChoice("Lucky Charm (75 gold)", "buy_lucky_charm"),
                    DialogueChoice("Card Pack (100 gold)", "buy_card_pack"),
                    DialogueChoice("Fortuna Shard (25 gold)", "buy_fortuna_shard"),
                    DialogueChoice("Nothing for now", "goodbye")
                ]
            ),
            "buy_healing_potion": DialogueNode(
                "buy_healing_potion",
                "This healing potion will restore your vitality during combat. Very useful!",
                [
                    DialogueChoice("I'll take it", "purchase_healing_potion"),
                    DialogueChoice("Show other items", "show_wares"),
                    DialogueChoice("Maybe later", "goodbye")
                ]
            ),
            "buy_lucky_charm": DialogueNode(
                "buy_lucky_charm",
                "This lucky charm improves your luck in card draws and combat!",
                [
                    DialogueChoice("I'll buy it", "purchase_lucky_charm"),
                    DialogueChoice("Show other items", "show_wares"),
                    DialogueChoice("Not interested", "goodbye")
                ]
            ),
            "buy_card_pack": DialogueNode(
                "buy_card_pack",
                "This pack contains 5 random cards. You might find something rare!",
                [
                    DialogueChoice("I'll take it", "purchase_card_pack"),
                    DialogueChoice("Show other items", "show_wares"),
                    DialogueChoice("Too expensive", "goodbye")
                ]
            ),
            "buy_fortuna_shard": DialogueNode(
                "buy_fortuna_shard",
                "Fortuna shards can be used for powerful upgrades!",
                [
                    DialogueChoice("I'll buy one", "purchase_fortuna_shard"),
                    DialogueChoice("Show other items", "show_wares"),
                    DialogueChoice("Not now", "goodbye")
                ]
            ),
            "purchase_healing_potion": DialogueNode(
                "purchase_healing_potion",
                "Excellent! The healing potion is yours. Use it wisely!",
                []
            ),
            "purchase_lucky_charm": DialogueNode(
                "purchase_lucky_charm",
                "The lucky charm is yours! May fortune smile upon you!",
                []
            ),
            "purchase_card_pack": DialogueNode(
                "purchase_card_pack",
                "Here's your card pack! Open it carefully!",
                []
            ),
            "purchase_fortuna_shard": DialogueNode(
                "purchase_fortuna_shard",
                "One Fortuna shard, freshly harvested!",
                []
            ),
            "goodbye": DialogueNode(
                "goodbye",
                "Come back anytime!",
                []
            )
        }
        
        merchant = NPC(
            npc_id="wandering_merchant",
            name="Wandering Merchant",
            npc_type=NPCType.MERCHANT,
            district=DistrictType.GRAND_TERMINAL,
            position=(5, 0.5, 10),
            dialogue_tree=merchant_dialogue,
            merchant=True,
            on_interact=self._merchant_interaction
        )
        self.npcs["wandering_merchant"] = merchant
        
        # Suspicious Intruder - Hostile NPC that attacks when confronted
        intruder_dialogue = {
            "greeting_first_time": DialogueNode(
                "greeting_first_time",
                "What do you want? I'm busy with... important work.",
                [
                    DialogueChoice("What kind of work?", "suspicious_response"),
                    DialogueChoice("You look familiar...", "recognition"),
                    DialogueChoice("Sorry to bother you", "goodbye")
                ]
            ),
            "suspicious_response": DialogueNode(
                "suspicious_response",
                "None of your business! The Chaos Dealers have plans, and you're not part of them. Now back off before I make you!",
                [
                    DialogueChoice("Chaos Dealers? Tell me more", "reveal_faction"),
                    DialogueChoice("I'll stop you!", "combat_start"),
                    DialogueChoice("Fine, I'll leave", "goodbye")
                ]
            ),
            "recognition": DialogueNode(
                "recognition",
                "Familiar? Ha! You must be thinking of someone else. Though... wait, you're not one of Valerius' lackeys, are you?",
                [
                    DialogueChoice("I work with the Syndicate", "syndicate_response"),
                    DialogueChoice("I work for no one", "independent_response")
                ]
            ),
            "reveal_faction": DialogueNode(
                "reveal_faction",
                "The Chaos Dealers seek to free this city from the Syndicate's tyranny! Order is a cage - we will unleash pure, beautiful chaos! And you... you're in our way!",
                [
                    DialogueChoice("I won't let you destroy the city", "combat_start")
                ]
            ),
            "syndicate_response": DialogueNode(
                "syndicate_response",
                "I knew it! Another puppet of that fool Valerius! Well, you won't be reporting back to him!",
                [
                    DialogueChoice("Prepare to fight!", "combat_start")
                ]
            ),
            "independent_response": DialogueNode(
                "independent_response",
                "Independent, eh? Then maybe you'd be interested in joining the winning side. The Chaos Dealers could use someone with your... talents.",
                [
                    DialogueChoice("Never! I'll stop you", "combat_start"),
                    DialogueChoice("Tell me more about your cause", "recruitment_attempt")
                ]
            ),
            "recruitment_attempt": DialogueNode(
                "recruitment_attempt",
                "Smart choice! The Syndicate has ruled through fear and control for too long. Join us, and help us bring true freedom to Aethelburg!",
                [
                    DialogueChoice("I refuse! Prepare to fight!", "combat_start"),
                    DialogueChoice("I need time to think", "goodbye")
                ]
            ),
            "combat_start": DialogueNode(
                "combat_start",
                "You've made your choice! For the glory of Chaos!",
                []
            ),
            "goodbye": DialogueNode(
                "goodbye",
                "Get out of here before I change my mind about letting you live.",
                []
            )
        }
        
        intruder = NPC(
            npc_id="suspicious_intruder",
            name="Suspicious Intruder",
            npc_type=NPCType.HOSTILE,
            district=DistrictType.GRAND_TERMINAL,
            position=(-8, 0.5, -12),
            dialogue_tree=intruder_dialogue,
            on_interact=self._intruder_interaction
        )
        self.npcs["suspicious_intruder"] = intruder
    
    def _start_arrival_quest(self):
        """Start the arrival quest when Valerius offers it."""
        self.quest_manager.start_quest("arrival")
        print("Quest started: Arrival in Aethelburg")
    
    def _purchase_tarot(self, tarot_id: str):
        """Handle Tarot card purchase."""
        print(f"Purchased {tarot_id} Tarot card!")
        # In a real implementation, this would add the item to player inventory
    
    def _on_valerius_interact(self):
        """Called when player interacts with Valerius."""
        print("Chairman Valerius acknowledges your presence.")
    
    def _on_cartomancer_interact(self):
        """Called when player interacts with the Cartomancer."""
        print("The Cartomancer's shop is filled with mysterious energy.")
    
    def _on_foreman_interact(self):
        """Called when player interacts with the Press Foreman."""
        print("The Twisted Press Foreman growls menacingly.")
    
    def _on_guardian_interact(self):
        """Called when player interacts with the Underdeck Guardian."""
        print("The Guardian's eyes gleam with hidden knowledge.")

    # Beggar NPC actions
    def _beggar_invite(self, player_stats=None):
        # This function will be called from the UI with access to player via external closure
        if player_stats:
            if 'beggar' not in player_stats.jokers:
                player_stats.jokers.append('beggar')
                print("The Beggar has joined your team as a companion!")
                print("You now have the Beggar joker ability!")
            else:
                print("The Beggar is already your companion.")
        else:
            print("If hooked with player, this would add the Beggar companion.")

    def _beggar_give(self, player_stats=None):
        if player_stats:
            take = min(player_stats.gold, 10)
            player_stats.gold -= take
            print(f"The Beggar takes {take} gold and thanks you.")
            # Give a small reward for generosity
            if take >= 5:
                print("The Beggar gives you a small blessing (+1 max HP)")
                player_stats.max_hp += 1
                player_stats.hp = min(player_stats.hp + 1, player_stats.max_hp)
        else:
            print("If hooked with player, this would transfer gold from player to beggar.")
    
    def get_npc_at_position(self, position: tuple, district: DistrictType) -> Optional[NPC]:
        """Get NPC at a specific position in a district."""
        for npc in self.npcs.values():
            if npc.district == district and npc.position == position:
                return npc
        return None
    
    def start_dialogue(self, npc_id: str) -> Optional[DialogueNode]:
        """Start dialogue with an NPC. Returns the first dialogue node."""
        if npc_id not in self.npcs:
            return None
        
        npc = self.npcs[npc_id]
        
        # Mark that player has met this NPC
        if not npc.met_player:
            npc.met_player = True
        
        # Get appropriate greeting
        greeting_id = npc.get_greeting_dialogue()
        
        if greeting_id in npc.dialogue_tree:
            self.current_dialogue = npc.dialogue_tree[greeting_id]
            self.dialogue_history = [greeting_id]
            return self.current_dialogue
        
        return None
    
    def make_choice(self, choice_index: int) -> Optional[DialogueNode]:
        """Make a dialogue choice. Returns the next dialogue node."""
        if not self.current_dialogue or choice_index >= len(self.current_dialogue.choices):
            return None
        
        choice = self.current_dialogue.choices[choice_index]
        
        # Execute choice action if present
        if choice.action:
            choice.action()
        
        # Check conditions
        if choice.condition and not choice.condition():
            return None
        
        # Move to next dialogue
        if choice.next_dialogue in self.current_dialogue.dialogue_tree:
            self.current_dialogue = self.current_dialogue.dialogue_tree[choice.next_dialogue]
            self.dialogue_history.append(choice.next_dialogue)
            return self.current_dialogue
        
        # End dialogue
        self.current_dialogue = None
        return None
    
    def end_dialogue(self):
        """End the current dialogue."""
        self.current_dialogue = None
        self.dialogue_history = []
    
    def get_npcs_in_district(self, district: DistrictType) -> List[NPC]:
        """Get all NPCs in a specific district."""
        return [npc for npc in self.npcs.values() if npc.district == district]
    
    def update_npc_quest_status(self, npc_id: str, quest_id: str, completed: bool = True):
        """Update an NPC's quest status."""
        if npc_id not in self.npcs:
            return
        
        npc = self.npcs[npc_id]
        
        if completed:
            npc.mark_quest_completed(quest_id)
        else:
            npc.mark_quest_given(quest_id)


class DialogueUI:
    """Simple dialogue UI for testing."""
    
    def __init__(self, dialogue_manager: DialogueManager):
        self.dialogue_manager = dialogue_manager
        self.current_npc: Optional[NPC] = None
    
    def start_dialogue(self, npc_id: str):
        """Start dialogue with an NPC."""
        self.current_npc = self.dialogue_manager.npcs.get(npc_id)
        if not self.current_npc:
            print(f"NPC {npc_id} not found!")
            return
        
        dialogue_node = self.dialogue_manager.start_dialogue(npc_id)
        if dialogue_node:
            self._display_dialogue(dialogue_node)
        else:
            print("Could not start dialogue.")
    
    def _display_dialogue(self, dialogue_node: DialogueNode):
        """Display a dialogue node."""
        print(f"\n{self.current_npc.name} ({dialogue_node.npc_emotion}):")
        print(f"\"{dialogue_node.text}\"")
        print("\nChoices:")
        
        for i, choice in enumerate(dialogue_node.choices):
            print(f"{i + 1}. {choice.text}")
        
        print("0. End dialogue")
    
    def make_choice(self, choice_index: int):
        """Make a dialogue choice."""
        if choice_index == 0:
            self.dialogue_manager.end_dialogue()
            self.current_npc = None
            print("Dialogue ended.")
            return
        
        choice_index -= 1  # Convert to 0-based index
        
        next_node = self.dialogue_manager.make_choice(choice_index)
        if next_node:
            self._display_dialogue(next_node)
        else:
            print("Dialogue ended.")
            self.current_npc = None


# Example usage and testing
if __name__ == "__main__":
    # Create world map and quest manager
    world_map = WorldMap()
    from quest_system import StoryManager, QuestManager
    story_manager = StoryManager(world_map)
    quest_manager = QuestManager(world_map, story_manager)
    
    # Create dialogue manager
    dialogue_manager = DialogueManager(quest_manager, world_map)
    
    # Create dialogue UI
    dialogue_ui = DialogueUI(dialogue_manager)
    
    # Test dialogue with Valerius
    print("Testing dialogue with Chairman Valerius...")
    dialogue_ui.start_dialogue("chairman_valerius")
    
    # Simulate choice 1 (Tell me about the Dissonance)
    dialogue_ui.make_choice(1)
    
    # Simulate choice 1 (How can I help?)
    dialogue_ui.make_choice(1)
    
    # Simulate choice 1 (I accept your offer)
    dialogue_ui.make_choice(1)
    
    print(f"Active quests: {len(quest_manager.get_active_quests())}") 

# Compatibility functions for existing ursina_game.py
def create_random_npc():
    """Compatibility function for existing code."""
    # Return a simple NPC for compatibility
    return NPC(
        npc_id="random_npc",
        name="Random NPC",
        npc_type=NPCType.STORY_NPC,
        district=DistrictType.GRAND_TERMINAL,
        position=(0, 1, 0),
        dialogue_tree={},
        on_interact=lambda: print("Random NPC interaction")
    )

 