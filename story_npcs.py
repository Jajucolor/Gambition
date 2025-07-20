from __future__ import annotations
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from world_system import world_state, ActProgress
import random


@dataclass
class DialogueOption:
    """A dialogue choice with conditions and consequences"""
    text: str
    condition: Optional[Callable[[Dict], bool]] = None
    consequence: Optional[Callable[[], None]] = None
    trust_change: int = 0
    leads_to: Optional[str] = None


@dataclass 
class DialogueNode:
    """A node in the dialogue tree"""
    speaker: str
    text: str
    options: List[DialogueOption]
    triggers_event: Optional[str] = None


class StoryNPC:
    """Base class for story-important NPCs"""
    
    def __init__(self, name: str, title: str, description: str):
        self.name = name
        self.title = title
        self.description = description
        self.dialogue_tree: Dict[str, DialogueNode] = {}
        self.current_node = "greeting"
        self.met_before = False
    
    def get_current_dialogue(self) -> DialogueNode:
        """Get the current dialogue node based on story state"""
        context = world_state.get_current_story_context()
        
        # Dynamic node selection based on story progress
        node_key = self._select_dialogue_node(context)
        return self.dialogue_tree.get(node_key, self.dialogue_tree["greeting"])
    
    def _select_dialogue_node(self, context: Dict) -> str:
        """Override in subclasses for character-specific logic"""
        return "greeting"
    
    def process_dialogue_choice(self, option_index: int) -> List[str]:
        """Process a dialogue choice and return story updates"""
        current_dialogue = self.get_current_dialogue()
        
        if option_index >= len(current_dialogue.options):
            return ["Invalid choice."]
        
        option = current_dialogue.options[option_index]
        updates = []
        
        # Check if option is available
        if option.condition:
            context = world_state.get_current_story_context()
            if not option.condition(context):
                return ["That option is not available right now."]
        
        # Apply consequences
        if option.consequence:
            option.consequence()
        
        # Apply trust changes
        if option.trust_change != 0:
            world_state.modify_valerius_trust(option.trust_change)
            if option.trust_change > 0:
                updates.append(f"[{self.name} seems more trusting]")
            else:
                updates.append(f"[{self.name} seems less trusting]")
        
        # Move to next node
        if option.leads_to:
            self.current_node = option.leads_to
        
        # Trigger story events
        if current_dialogue.triggers_event:
            story_updates = world_state.advance_story(current_dialogue.triggers_event)
            updates.extend(story_updates)
        
        return updates


class ChairmanValerius(StoryNPC):
    """The main antagonist and apparent ally"""
    
    def __init__(self):
        super().__init__(
            "Chairman Valerius", 
            "Leader of the Syndicate of Providence",
            "An impeccably dressed man with piercing eyes and a warm smile that doesn't quite reach them."
        )
        self._build_dialogue_tree()
    
    def _build_dialogue_tree(self):
        # First meeting
        self.dialogue_tree["greeting"] = DialogueNode(
            speaker="Valerius",
            text="Ah, you must be the one who caused such a stir at the Grand Terminal. Your... unique talents have not gone unnoticed. I am Chairman Valerius, and I believe you may be exactly what Aethelburg needs in these dark times.",
            options=[
                DialogueOption(
                    text="What do you mean by 'unique talents'?",
                    leads_to="explain_talents"
                ),
                DialogueOption(
                    text="Tell me about this 'Dissonance' I keep hearing about.",
                    leads_to="explain_dissonance"
                ),
                DialogueOption(
                    text="I'm looking for someone - a gambler called Maestro.",
                    trust_change=-5,
                    leads_to="maestro_inquiry"
                )
            ]
        )
        
        self.dialogue_tree["explain_talents"] = DialogueNode(
            speaker="Valerius", 
            text="You fought through the Twisted without succumbing to the Dissonance yourself. Most remarkable. The corrupted Fortuna that twists others seems to... bend around you. You're immune, and more than that - you can channel pure luck itself.",
            options=[
                DialogueOption(
                    text="How do you know all this?",
                    leads_to="syndicate_knowledge"
                ),
                DialogueOption(
                    text="What's this Dissonance you mentioned?",
                    leads_to="explain_dissonance"
                )
            ]
        )
        
        self.dialogue_tree["explain_dissonance"] = DialogueNode(
            speaker="Valerius",
            text="A plague upon our fair city. The Fortuna that once brought prosperity now emanates a... discordant frequency. It warps people's deepest desires into monstrous forms. The greedy become creatures of endless hunger, the proud become towers of crystalline vanity.",
            options=[
                DialogueOption(
                    text="How can I help stop it?",
                    trust_change=10,
                    leads_to="recruitment"
                ),
                DialogueOption(
                    text="This sounds like something the Syndicate should handle.",
                    trust_change=-5,
                    leads_to="syndicate_responsibility"
                )
            ],
            triggers_event="meet_valerius"
        )
        
        self.dialogue_tree["maestro_inquiry"] = DialogueNode(
            speaker="Valerius",
            text="Maestro... yes, I recall the name. A talented individual, but he became... obsessed with conspiracy theories about the Syndicate. He disappeared some months ago. Perhaps he fell victim to the very Dissonance he claimed to be investigating.",
            options=[
                DialogueOption(
                    text="I don't believe that. What really happened to him?",
                    trust_change=-10,
                    leads_to="maestro_suspicion"
                ),
                DialogueOption(
                    text="I see. Then I'll need to find answers myself.",
                    leads_to="independent_investigation"
                )
            ]
        )
        
        self.dialogue_tree["recruitment"] = DialogueNode(
            speaker="Valerius",
            text="Excellent. I believe the source is a corrupted Fortuna node - what I call the 'Heart of Chaos.' With your immunity, you could reach it and purify the source. Take this deck - it will help you channel your power more effectively.",
            options=[
                DialogueOption(
                    text="I accept this mission.",
                    trust_change=15,
                    leads_to="mission_accepted"
                ),
                DialogueOption(
                    text="I'll consider it, but I have questions first.",
                    leads_to="more_questions"
                )
            ]
        )
    
    def _select_dialogue_node(self, context: Dict) -> str:
        # Dynamic dialogue based on story progress
        if not context["flags"]["met_valerius"]:
            return "greeting"
        elif context["act"] == ActProgress.ACT_2_TURN:
            if context["maestro_clues"] >= 2:
                return "act2_suspicion"
            else:
                return "act2_progress"
        elif context["act"] == ActProgress.ACT_3_RIVER:
            return "act3_confrontation"
        else:
            return "mission_progress"


class TheCartomancer(StoryNPC):
    """The mysterious tarot card dealer who knows more than she lets on"""
    
    def __init__(self):
        super().__init__(
            "The Cartomancer",
            "Keeper of Hidden Truths", 
            "A woman shrouded in veils and mystery, her eyes seem to see through time itself."
        )
        self._build_dialogue_tree()
    
    def _build_dialogue_tree(self):
        self.dialogue_tree["greeting"] = DialogueNode(
            speaker="Cartomancer",
            text="Ah, the Ace arrives at last. I have been expecting you, though perhaps not in the way you think. The cards whispered of your coming long before you set foot in this cursed city.",
            options=[
                DialogueOption(
                    text="You know who I am?",
                    leads_to="identity_hints"
                ),
                DialogueOption(
                    text="I need tarot cards for my deck.",
                    leads_to="shop_cards"
                ),
                DialogueOption(
                    text="What do you know about Maestro?",
                    condition=lambda ctx: ctx["maestro_clues"] > 0,
                    leads_to="maestro_truth"
                )
            ]
        )
        
        self.dialogue_tree["identity_hints"] = DialogueNode(
            speaker="Cartomancer",
            text="The cards speak of a soul born not of flesh, but of crystallized fortune itself. They whisper of a creator who loved his creation too much, and a puppet master who pulls strings from shadows. But the future... the future remains unwritten.",
            options=[
                DialogueOption(
                    text="That doesn't make sense. I remember my childhood...",
                    leads_to="false_memories"
                ),
                DialogueOption(
                    text="You're speaking in riddles.",
                    leads_to="riddle_explanation"
                )
            ]
        )
        
        self.dialogue_tree["maestro_truth"] = DialogueNode(
            speaker="Cartomancer",
            text="Your 'mentor' was more than teacher - he was creator, father, and ultimately, protector. The cards show his sacrifice, his love, and his imprisonment. But they also show... hope. Not all is as the Chairman would have you believe.",
            options=[
                DialogueOption(
                    text="Where is Maestro now?",
                    leads_to="maestro_location"
                ),
                DialogueOption(
                    text="What sacrifice? What do you mean 'creator'?",
                    leads_to="creation_truth"
                )
            ]
        )
    
    def _select_dialogue_node(self, context: Dict) -> str:
        if context["act"] == ActProgress.ACT_3_RIVER:
            return "final_truth"
        elif context["flags"]["discovered_ascendancy_engine"]:
            return "engine_knowledge"
        elif context["maestro_clues"] >= 2:
            return "maestro_truth"
        else:
            return "greeting"


class SyndicateScientist(StoryNPC):
    """A nervous Syndicate researcher who provides exposition about Fortuna"""
    
    def __init__(self):
        super().__init__(
            "Dr. Flemming",
            "Fortuna Research Specialist",
            "A nervous man in a lab coat, constantly adjusting his spectacles and glancing around anxiously."
        )
        self._build_dialogue_tree()
    
    def _build_dialogue_tree(self):
        self.dialogue_tree["greeting"] = DialogueNode(
            speaker="Dr. Flemming",
            text="Oh! You're the new operative Chairman Valerius mentioned. I... I'm not supposed to talk about the research, but if the Chairman sent you...",
            options=[
                DialogueOption(
                    text="Tell me about Fortuna.",
                    leads_to="fortuna_explanation"
                ),
                DialogueOption(
                    text="What research aren't you supposed to talk about?",
                    trust_change=-5,
                    leads_to="forbidden_research"
                ),
                DialogueOption(
                    text="Have you heard of something called the Ascendancy Engine?",
                    condition=lambda ctx: ctx["maestro_clues"] >= 2,
                    leads_to="engine_reaction"
                )
            ]
        )


# NPC Registry
STORY_NPCS: Dict[str, StoryNPC] = {
    "valerius": ChairmanValerius(),
    "cartomancer": TheCartomancer(), 
    "syndicate_scientist": SyndicateScientist(),
}


def get_npc_dialogue(npc_id: str) -> Optional[DialogueNode]:
    """Get the current dialogue for an NPC"""
    if npc_id in STORY_NPCS:
        return STORY_NPCS[npc_id].get_current_dialogue()
    return None


def process_npc_choice(npc_id: str, choice_index: int) -> List[str]:
    """Process a dialogue choice with an NPC"""
    if npc_id in STORY_NPCS:
        return STORY_NPCS[npc_id].process_dialogue_choice(choice_index)
    return ["NPC not found."] 