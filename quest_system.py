from __future__ import annotations
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
from world_map import WorldMap, DistrictType
import time


class QuestType(Enum):
    """Types of quests in the game."""
    MAIN_QUEST = "main_quest"
    SIDE_QUEST = "side_quest"
    COMPANION_QUEST = "companion_quest"
    WORLD_QUEST = "world_quest"


class QuestStatus(Enum):
    """Status of a quest."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ActType(Enum):
    """The three main acts of the story."""
    ACT_I = "act_i"      # The Ante - Arrival and setup
    ACT_II = "act_ii"     # The Turn - Investigation and discovery
    ACT_III = "act_iii"   # The River - Confrontation and choice


@dataclass
class QuestObjective:
    """A single objective within a quest."""
    id: str
    description: str
    completed: bool = False
    required_count: int = 1
    current_count: int = 0
    
    def update_progress(self, amount: int = 1) -> bool:
        """Update progress and return True if completed."""
        self.current_count = min(self.current_count + amount, self.required_count)
        if self.current_count >= self.required_count and not self.completed:
            self.completed = True
            return True
        return False


@dataclass
class QuestReward:
    """Rewards for completing a quest."""
    gold: int = 0
    fortunas: int = 0
    items: List[str] = None
    companions: List[str] = None
    district_unlocks: List[DistrictType] = None
    story_progress: int = 0
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.companions is None:
            self.companions = []
        if self.district_unlocks is None:
            self.district_unlocks = []


class Quest:
    """Represents a quest in the game."""
    
    def __init__(self,
                 quest_id: str,
                 title: str,
                 description: str,
                 quest_type: QuestType,
                 act: ActType,
                 objectives: List[QuestObjective],
                 rewards: QuestReward,
                 prerequisites: List[str] = None,
                 on_start: Callable = None,
                 on_complete: Callable = None,
                 on_fail: Callable = None):
        
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.quest_type = quest_type
        self.act = act
        self.objectives = objectives
        self.rewards = rewards
        self.prerequisites = prerequisites or []
        self.on_start = on_start
        self.on_complete = on_complete
        self.on_fail = on_fail
        
        self.status = QuestStatus.NOT_STARTED
        self.started_time: Optional[float] = None
        self.completed_time: Optional[float] = None
    
    def can_start(self, completed_quests: List[str]) -> bool:
        """Check if this quest can be started."""
        return all(prereq in completed_quests for prereq in self.prerequisites)
    
    def start_quest(self) -> bool:
        """Start the quest. Returns True if successful."""
        if self.status != QuestStatus.NOT_STARTED:
            return False
        
        self.status = QuestStatus.ACTIVE
        self.started_time = time.time()
        
        if self.on_start:
            self.on_start()
        
        print(f"Quest started: {self.title}")
        return True
    
    def update_objective(self, objective_id: str, progress: int = 1) -> bool:
        """Update progress on an objective. Returns True if quest is completed."""
        for objective in self.objectives:
            if objective.id == objective_id and not objective.completed:
                if objective.update_progress(progress):
                    print(f"Objective completed: {objective.description}")
                
                # Check if all objectives are complete
                if all(obj.completed for obj in self.objectives):
                    return self.complete_quest()
        
        return False
    
    def complete_quest(self) -> bool:
        """Complete the quest. Returns True if successful."""
        if self.status != QuestStatus.ACTIVE:
            return False
        
        self.status = QuestStatus.COMPLETED
        self.completed_time = time.time()
        
        # Note: completion callback is handled by QuestManager
        print(f"Quest completed: {self.title}")
        return True
    
    def fail_quest(self) -> bool:
        """Fail the quest. Returns True if successful."""
        if self.status != QuestStatus.ACTIVE:
            return False
        
        self.status = QuestStatus.FAILED
        
        if self.on_fail:
            self.on_fail()
        
        print(f"Quest failed: {self.title}")
        return True
    
    def get_progress(self) -> Dict[str, Any]:
        """Get quest progress information."""
        completed = sum(1 for obj in self.objectives if obj.completed)
        total = len(self.objectives)
        
        return {
            'completed_objectives': completed,
            'total_objectives': total,
            'progress_percentage': (completed / total) * 100 if total > 0 else 0,
            'status': self.status.value
        }
    
    def get_objective_summary(self) -> str:
        """Get a human-readable summary of quest objectives."""
        if not self.objectives:
            return "No objectives"
        
        summary_parts = []
        for obj in self.objectives:
            if obj.completed:
                summary_parts.append(f"✓ {obj.description}")
            else:
                if obj.required_count > 1:
                    summary_parts.append(f"• {obj.description} ({obj.current_count}/{obj.required_count})")
                else:
                    summary_parts.append(f"• {obj.description}")
        
        return "\n".join(summary_parts)


class StoryManager:
    """Manages the main story progression and acts."""
    
    def __init__(self, world_map: WorldMap):
        self.world_map = world_map
        self.current_act = ActType.ACT_I
        self.act_progress: Dict[ActType, float] = {act: 0.0 for act in ActType}
        self.major_events: Dict[str, bool] = {}
        
        # Story flags and triggers
        self.story_flags: Dict[str, bool] = {}
        self.triggered_events: List[str] = []
        
        # Act-specific quests and events
        self.act_quests: Dict[ActType, List[str]] = {
            ActType.ACT_I: [],
            ActType.ACT_II: [],
            ActType.ACT_III: []
        }
    
    def get_act_description(self, act: ActType) -> str:
        """Get the description of an act."""
        descriptions = {
            ActType.ACT_I: "The Ante - Your arrival in Aethelburg and first encounters with the Dissonance.",
            ActType.ACT_II: "The Turn - Uncovering the truth behind the Syndicate and the Ascendancy Engine.",
            ActType.ACT_III: "The River - The final confrontation with Chairman Valerius and your destiny."
        }
        return descriptions.get(act, "Unknown act")
    
    def advance_act(self, new_act: ActType) -> bool:
        """Advance to a new act. Returns True if successful."""
        if new_act.value <= self.current_act.value:
            return False
        
        old_act = self.current_act
        self.current_act = new_act
        
        print(f"Advancing to {new_act.value.upper()}: {self.get_act_description(new_act)}")
        
        # Trigger act-specific events
        self._trigger_act_events(new_act)
        
        return True
    
    def _trigger_act_events(self, act: ActType):
        """Trigger events specific to an act."""
        if act == ActType.ACT_II:
            # Unlock more districts and reveal the truth
            self.world_map.unlock_district(DistrictType.PRINTING_PRESS_QUARTER)
            self.world_map.unlock_district(DistrictType.THE_UNDERDECK)
            print("The truth begins to surface...")
            
        elif act == ActType.ACT_III:
            # Unlock final areas
            self.world_map.unlock_district(DistrictType.QUARANTINE_ZONE)
            self.world_map.unlock_district(DistrictType.SYNDICATE_HEADQUARTERS)
            print("The final confrontation approaches...")
    
    def trigger_story_event(self, event_id: str) -> bool:
        """Trigger a major story event. Returns True if successful."""
        if event_id in self.triggered_events:
            return False
        
        self.triggered_events.append(event_id)
        self.story_flags[event_id] = True
        
        print(f"Story event triggered: {event_id}")
        return True
    
    def get_act_progress(self, act: ActType) -> float:
        """Get the progress percentage for a specific act."""
        if act == ActType.ACT_I:
            # Act I progress based on arrival quest completion
            return 0.5 if "met_valerius" in self.story_flags else 0.0
        elif act == ActType.ACT_II:
            # Act II progress based on truth quest completion
            return 0.7 if "truth_revealed" in self.story_flags else 0.0
        elif act == ActType.ACT_III:
            # Act III progress based on final choice readiness
            return 0.9 if "final_choice_ready" in self.story_flags else 0.0
        return 0.0
    
    def get_next_milestone(self) -> str:
        """Get the next story milestone to achieve."""
        if self.current_act == ActType.ACT_I:
            if "met_valerius" not in self.story_flags:
                return "Meet Chairman Valerius at the Casino District"
            else:
                return "Complete the Casino District investigation"
        elif self.current_act == ActType.ACT_II:
            if "truth_revealed" not in self.story_flags:
                return "Uncover the truth about the Dissonance"
            else:
                return "Recruit allies in The Underdeck"
        elif self.current_act == ActType.ACT_III:
            if "final_choice_ready" not in self.story_flags:
                return "Confront Chairman Valerius"
            else:
                return "Make your final choice"
        return "Explore the world to discover new objectives"


class QuestManager:
    """Manages all quests in the game."""
    
    def __init__(self, world_map: WorldMap, story_manager: StoryManager):
        self.world_map = world_map
        self.story_manager = story_manager
        
        # Quest storage
        self.available_quests: Dict[str, Quest] = {}
        self.active_quests: Dict[str, Quest] = {}
        self.completed_quests: List[str] = []
        self.failed_quests: List[str] = []
        
        # Initialize all quests
        self._initialize_quests()
    
    def _initialize_quests(self):
        """Initialize all quests in the game."""
        
        # ACT I QUESTS
        
        # Tutorial Quest: First Encounter
        tutorial_quest = Quest(
            quest_id="tutorial",
            title="First Encounter",
            description="A suspicious intruder lurks nearby. Defeat them to prove your combat skills.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_I,
            objectives=[
                QuestObjective("defeat_intruder", "Defeat the Suspicious Intruder", required_count=1)
            ],
            rewards=QuestReward(
                gold=20,
                fortunas=5,
                story_progress=1
            ),
            on_complete=self._create_completion_callback("tutorial")
        )
        self.available_quests["tutorial"] = tutorial_quest
        
        # Main Quest: Meet the Chairman
        meet_chairman_quest = Quest(
            quest_id="meet_chairman",
            title="Meet the Chairman",
            description="Find Chairman Valerius to understand what's happening in Aethelburg.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_I,
            objectives=[
                QuestObjective("find_valerius", "Find and speak with Chairman Valerius"),
                QuestObjective("receive_joker", "Accept The Joker companion from Valerius")
            ],
            rewards=QuestReward(
                gold=30,
                fortunas=10,
                story_progress=2
            ),
            prerequisites=["tutorial"],
            on_complete=self._create_completion_callback("meet_chairman")
        )
        self.available_quests["meet_chairman"] = meet_chairman_quest
        
        # Main Quest: Clear the Terminal
        clear_terminal_quest = Quest(
            quest_id="clear_terminal",
            title="Clear the Terminal",
            description="Chairman Valerius has tasked you with clearing the Twisted guards from the Grand Terminal.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_I,
            objectives=[
                QuestObjective("kill_twisted", "Defeat 3 Twisted guards at the terminal", required_count=3),
                QuestObjective("return_to_valerius", "Return to Chairman Valerius")
            ],
            rewards=QuestReward(
                gold=50,
                fortunas=15,
                district_unlocks=[DistrictType.CASINO_DISTRICT],
                story_progress=3
            ),
            prerequisites=["meet_chairman"],
            on_complete=self._create_completion_callback("clear_terminal")
        )
        self.available_quests["clear_terminal"] = clear_terminal_quest
        
        # Main Quest: First Investigation
        investigation_quest = Quest(
            quest_id="first_investigation",
            title="The Syndicate's Request",
            description="Valerius has identified the Casino District as a source of Dissonance. Investigate and eliminate the corruption there.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_I,
            objectives=[
                QuestObjective("explore_casino", "Enter and explore the Casino District", required_count=1),
                QuestObjective("defeat_casino_boss", "Defeat the Twisted casino manager", required_count=1),
                QuestObjective("collect_fortuna", "Collect 20 Fortuna shards from corrupted areas", required_count=20)
            ],
            rewards=QuestReward(
                gold=100,
                fortunas=25,
                district_unlocks=[DistrictType.GILDED_PROMENADE],
                story_progress=2
            ),
            prerequisites=["clear_terminal"],
            on_complete=self._create_completion_callback("first_investigation")
        )
        
        # Add boss encounter trigger
        investigation_quest.boss_trigger = "casino_manager"
        self.available_quests["first_investigation"] = investigation_quest
        
        # Side Quest: The Cartomancer
        cartomancer_quest = Quest(
            quest_id="meet_cartomancer",
            title="The Mysterious Cartomancer",
            description="Find the Cartomancer in the Gilded Promenade and learn about Tarot cards.",
            quest_type=QuestType.SIDE_QUEST,
            act=ActType.ACT_I,
            objectives=[
                QuestObjective("find_shop", "Find the Cartomancer's hidden shop"),
                QuestObjective("purchase_tarot", "Purchase your first Tarot card"),
                QuestObjective("learn_lore", "Learn about the history of Tarot in Aethelburg")
            ],
            rewards=QuestReward(
                gold=25,
                fortunas=5,
                items=["the_sun_tarot"]
            )
        )
        self.available_quests["meet_cartomancer"] = cartomancer_quest
        
        # ACT II QUESTS
        
        # Main Quest: Uncovering the Truth
        truth_quest = Quest(
            quest_id="uncovering_truth",
            title="Uncovering the Truth",
            description="Investigate the Printing Press Quarter and discover the real nature of the Dissonance.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_II,
            objectives=[
                QuestObjective("explore_press_quarter", "Explore the Printing Press Quarter"),
                QuestObjective("investigate_press", "Investigate the Printing Press operations"),
                QuestObjective("defeat_press_boss", "Defeat the Twisted press foreman"),
                QuestObjective("learn_ascendancy", "Learn about the Ascendancy Engine project")
            ],
            rewards=QuestReward(
                gold=150,
                fortunas=40,
                district_unlocks=[DistrictType.THE_UNDERDECK],
                story_progress=3
            ),
            prerequisites=["first_investigation"],
            on_complete=self._create_completion_callback("uncovering_truth")
        )
        self.available_quests["uncovering_truth"] = truth_quest
        
        # Main Quest: The Underdeck
        underdeck_quest = Quest(
            quest_id="underdeck_investigation",
            title="The Underdeck",
            description="Explore The Underdeck and recruit powerful Jokers to your cause.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_II,
            objectives=[
                QuestObjective("explore_underdeck", "Explore The Underdeck"),
                QuestObjective("recruit_jokers", "Recruit 3 Jokers to your party"),
                QuestObjective("learn_maestro", "Learn about your mentor Maestro's disappearance"),
                QuestObjective("defeat_underdeck_boss", "Defeat the Underdeck's guardian")
            ],
            rewards=QuestReward(
                gold=200,
                fortunas=50,
                companions=["fortune_teller", "berserker", "echo_mage"],
                story_progress=4
            ),
            prerequisites=["uncovering_truth"],
            on_complete=self._create_completion_callback("underdeck_investigation")
        )
        self.available_quests["underdeck_investigation"] = underdeck_quest
        
        # ACT III QUESTS
        
        # Main Quest: The Final Confrontation
        final_quest = Quest(
            quest_id="final_confrontation",
            title="The Final Confrontation",
            description="Breach the Syndicate Headquarters and confront Chairman Valerius.",
            quest_type=QuestType.MAIN_QUEST,
            act=ActType.ACT_III,
            objectives=[
                QuestObjective("reach_headquarters", "Reach the Syndicate Headquarters"),
                QuestObjective("navigate_palace", "Navigate through the palace defenses"),
                QuestObjective("confront_valerius", "Confront Chairman Valerius"),
                QuestObjective("learn_truth", "Learn the truth about your origin"),
                QuestObjective("defeat_valerius", "Defeat Chairman Valerius in combat")
            ],
            rewards=QuestReward(
                gold=500,
                fortunas=100,
                story_progress=5
            ),
            prerequisites=["underdeck_investigation"],
            on_complete=self._create_completion_callback("final_confrontation")
        )
        self.available_quests["final_confrontation"] = final_quest
    
    def _create_completion_callback(self, quest_id: str):
        """Create a completion callback for a specific quest."""
        def callback():
            if quest_id == "tutorial":
                self._on_tutorial_complete()
            elif quest_id == "meet_chairman":
                self._on_meet_chairman_complete()
            elif quest_id == "clear_terminal":
                self._on_clear_terminal_complete()
            elif quest_id == "first_investigation":
                self._on_investigation_complete()
            elif quest_id == "uncovering_truth":
                self._on_truth_complete()
            elif quest_id == "underdeck_investigation":
                self._on_underdeck_complete()
            elif quest_id == "final_confrontation":
                self._on_final_complete()
            else:
                print(f"No completion callback defined for quest: {quest_id}")
        return callback
    
    def _on_tutorial_complete(self):
        """Called when the tutorial quest is completed."""
        print("=== QUEST COMPLETION: First Encounter ===")
        print("Well done! You've proven your combat skills.")
        print("Now find Chairman Valerius to learn more about the situation.")
        
        # Automatically start the next quest
        if "meet_chairman" in self.available_quests:
            if self.start_quest("meet_chairman"):
                print("✓ New quest started: Meet the Chairman")
    
    def _on_meet_chairman_complete(self):
        """Called when the meet chairman quest is completed."""
        print("=== QUEST COMPLETION: Meet the Chairman ===")
        print("Chairman Valerius has briefed you on the situation.")
        print("You received The Joker companion!")
        print("You now have a mission to clear the Twisted guards from the terminal.")
        
        # The Joker is given directly during NPC interaction
        
        # Trigger story event
        self.story_manager.trigger_story_event("met_valerius")
        
        # Automatically start the next quest
        if "clear_terminal" in self.available_quests:
            if self.start_quest("clear_terminal"):
                print("✓ New quest started: Clear the Terminal")
    
    def _on_clear_terminal_complete(self):
        """Called when the clear terminal quest is completed."""
        print("=== QUEST COMPLETION: Clear the Terminal ===")
        print("You have successfully cleared the Twisted guards from the Grand Terminal.")
        print("Chairman Valerius is pleased with your work.")
        print("The Casino District is now unlocked!")
        
        # Automatically start the next quest
        if "first_investigation" in self.available_quests:
            if self.start_quest("first_investigation"):
                print("✓ New quest started: The Syndicate's Request")
    
    def _on_arrival_complete(self):
        """Called when the arrival quest is completed."""
        print("=== QUEST COMPLETION: Arrival in Aethelburg ===")
        print("You have successfully arrived in Aethelburg and met Chairman Valerius.")
        print("The Casino District is now unlocked!")
        
        # Trigger story event
        self.story_manager.trigger_story_event("met_valerius")
        
        # Automatically start the next quest
        print(f"Available quests: {list(self.available_quests.keys())}")
        print(f"Completed quests: {self.completed_quests}")
        
        if "first_investigation" in self.available_quests:
            print("Attempting to start first_investigation quest...")
            if self.start_quest("first_investigation"):
                print("✓ New quest started: The Syndicate's Request")
            else:
                print("✗ Failed to start first_investigation quest")
                # Check prerequisites
                quest = self.available_quests["first_investigation"]
                print(f"Prerequisites: {quest.prerequisites}")
                print(f"Can start: {quest.can_start(self.completed_quests)}")
        else:
            print("✗ first_investigation quest not found in available quests")
    
    def _on_investigation_complete(self):
        """Called when the first investigation quest is completed."""
        print("You have completed your first investigation for the Syndicate.")
        print("The Gilded Promenade is now unlocked!")
        
        # Trigger story event
        self.story_manager.trigger_story_event("first_investigation_complete")
        
        # Automatically start the next quest
        if "uncovering_truth" in self.available_quests:
            self.start_quest("uncovering_truth")
            print("New quest started: Uncovering the Truth")
    
    def _on_truth_complete(self):
        """Called when the truth quest is completed."""
        print("You have uncovered the first hints of the truth about the Dissonance.")
        print("The Underdeck is now unlocked!")
        
        # Advance to Act II
        self.story_manager.advance_act(ActType.ACT_II)
        self.story_manager.trigger_story_event("truth_revealed")
        
        # Automatically start the next quest
        if "underdeck_investigation" in self.available_quests:
            self.start_quest("underdeck_investigation")
            print("New quest started: The Underdeck Investigation")
    
    def _on_underdeck_complete(self):
        """Called when the underdeck quest is completed."""
        print("You have recruited powerful allies and learned about Maestro.")
        print("The final confrontation approaches...")
        
        # Advance to Act III
        self.story_manager.advance_act(ActType.ACT_III)
        self.story_manager.trigger_story_event("ready_for_confrontation")
        
        # Automatically start the final quest
        if "final_confrontation" in self.available_quests:
            self.start_quest("final_confrontation")
            print("New quest started: The Final Confrontation")
    
    def _on_final_complete(self):
        """Called when the final quest is completed."""
        print("You have confronted Chairman Valerius and learned the truth.")
        print("The final choice awaits...")
        
        self.story_manager.trigger_story_event("final_choice_ready")
    
    def start_quest(self, quest_id: str) -> bool:
        """Start a quest. Returns True if successful."""
        if quest_id not in self.available_quests:
            return False
        
        quest = self.available_quests[quest_id]
        
        if not quest.can_start(self.completed_quests):
            return False
        
        if quest.start_quest():
            self.active_quests[quest_id] = quest
            return True
        
        return False
    
    def update_quest_progress(self, quest_id: str, objective_id: str, progress: int = 1) -> bool:
        """Update progress on a quest objective. Returns True if quest completed."""
        if quest_id not in self.active_quests:
            print(f"Quest {quest_id} not found in active quests: {list(self.active_quests.keys())}")
            return False
        
        quest = self.active_quests[quest_id]
        print(f"Updating quest progress: {quest_id} - {objective_id} (+{progress})")
        
        if quest.update_objective(objective_id, progress):
            # Quest completed - mark as completed FIRST
            print(f"=== QUEST COMPLETED: {quest.title} ===")
            self.completed_quests.append(quest_id)
            del self.active_quests[quest_id]
            
            # Apply rewards
            self._apply_quest_rewards(quest.rewards)
            
            print(f"Quest {quest_id} moved to completed quests: {self.completed_quests}")
            
            # THEN call the completion callback (after quest is marked complete)
            if quest.on_complete:
                print(f"Calling completion callback for {quest_id}")
                quest.on_complete()
            
            return True
        else:
            # Show current progress
            progress_info = quest.get_progress()
            print(f"Quest progress: {progress_info['completed_objectives']}/{progress_info['total_objectives']} objectives completed")
        
        return False
    
    def get_next_quest_hint(self) -> str:
        """Get a hint for what the player should do next."""
        # Check if there are any active quests
        if self.active_quests:
            active_quest = list(self.active_quests.values())[0]
            # Get the first incomplete objective
            for objective in active_quest.objectives:
                if not objective.completed:
                    return f"Active: {objective.description}"
            return "Return to quest giver to complete quest"
        
        # Check if there are available quests that can be started
        available = self.get_available_quests()
        if available:
            next_quest = available[0]
            return f"Available: {next_quest.title}"
        
        # No active or available quests
        return "Explore the world to discover new opportunities"
    
    def _apply_quest_rewards(self, rewards: QuestReward):
        """Apply quest rewards to the player."""
        if rewards.gold > 0:
            print(f"Earned {rewards.gold} gold!")
        
        if rewards.fortunas > 0:
            print(f"Earned {rewards.fortunas} Fortuna shards!")
        
        if rewards.items:
            for item in rewards.items:
                print(f"Obtained: {item}")
        
        if rewards.companions:
            for companion in rewards.companions:
                print(f"Recruited: {companion}")
        
        if rewards.district_unlocks:
            for district in rewards.district_unlocks:
                self.world_map.unlock_district(district)
        
        if rewards.story_progress > 0:
            print("Story progress advanced!")
    
    def get_available_quests(self) -> List[Quest]:
        """Get all quests that can be started."""
        available = []
        
        for quest in self.available_quests.values():
            if quest.status == QuestStatus.NOT_STARTED and quest.can_start(self.completed_quests):
                available.append(quest)
        
        return available
    
    def get_active_quests(self) -> List[Quest]:
        """Get all currently active quests."""
        return list(self.active_quests.values())
    
    def get_quest_progress(self) -> Dict[str, Any]:
        """Get overall quest progress information."""
        total_quests = len(self.available_quests)
        completed_quests = len(self.completed_quests)
        active_quests = len(self.active_quests)
        
        return {
            'total_quests': total_quests,
            'completed_quests': completed_quests,
            'active_quests': active_quests,
            'completion_percentage': (completed_quests / total_quests) * 100 if total_quests > 0 else 0
        }
    
    def get_next_quest_hint(self) -> str:
        """Get a hint about what to do next."""
        if self.active_quests:
            # Return hint for current active quest
            quest = list(self.active_quests.values())[0]
            incomplete_objectives = [obj for obj in quest.objectives if not obj.completed]
            if incomplete_objectives:
                return f"Current quest: {quest.title} - {incomplete_objectives[0].description}"
            else:
                return f"Complete quest: {quest.title}"
        
        # Check for available quests
        available = self.get_available_quests()
        if available:
            return f"Available quest: {available[0].title} - {available[0].description[:60]}..."
        
        # Check for completed quests that might unlock new content
        if self.completed_quests:
            return "All quests completed! Explore the world for new discoveries."
        
        return "No quests available. Explore the world to find new objectives."


# Example usage and testing
if __name__ == "__main__":
    # Create world map and story manager
    world_map = WorldMap()
    story_manager = StoryManager(world_map)
    
    # Create quest manager
    quest_manager = QuestManager(world_map, story_manager)
    
    # Start the arrival quest
    quest_manager.start_quest("arrival")
    
    # Update progress
    quest_manager.update_quest_progress("arrival", "fight_twisted", 1)
    quest_manager.update_quest_progress("arrival", "fight_twisted", 1)
    quest_manager.update_quest_progress("arrival", "fight_twisted", 1)
    
    print(f"Active quests: {len(quest_manager.get_active_quests())}")
    print(f"Available quests: {len(quest_manager.get_available_quests())}") 