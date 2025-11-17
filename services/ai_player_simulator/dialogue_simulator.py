"""
AI Player simulator for testing localized dialogue flows.
Implements TML-08 (R-ML-QA-003).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import random
import json
import re

logger = logging.getLogger(__name__)


class PlayerPersonality(str, Enum):
    """AI player personality types."""
    EXPLORER = "explorer"      # Tries all dialogue options
    SPEEDRUNNER = "speedrunner"  # Takes shortest path
    COMPLETIONIST = "completionist"  # Exhausts all branches
    RANDOM = "random"         # Random choices
    EVIL = "evil"            # Always picks "evil" options
    GOOD = "good"            # Always picks "good" options
    CHAOTIC = "chaotic"      # Unpredictable choices


class DialogueIssueType(str, Enum):
    """Types of dialogue issues detected."""
    MISSING_TRANSLATION = "missing_translation"
    BROKEN_BRANCH = "broken_branch"
    INFINITE_LOOP = "infinite_loop"
    DEAD_END = "dead_end"
    CONTEXT_ERROR = "context_error"
    GENDER_MISMATCH = "gender_mismatch"
    TONE_INCONSISTENCY = "tone_inconsistency"
    CULTURAL_ISSUE = "cultural_issue"
    VARIABLE_ERROR = "variable_error"
    TIMING_ISSUE = "timing_issue"


@dataclass
class DialogueNode:
    """A node in the dialogue tree."""
    node_id: str
    speaker_id: str
    localization_key: str
    
    # Choices that lead to other nodes
    choices: List['DialogueChoice'] = field(default_factory=list)
    
    # Conditions for this node to appear
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # State changes when this node is visited
    state_changes: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    tags: Set[str] = field(default_factory=set)
    audio_duration: Optional[float] = None
    is_terminal: bool = False


@dataclass
class DialogueChoice:
    """A choice in dialogue."""
    choice_id: str
    localization_key: str
    target_node_id: str
    
    # Conditions for this choice to appear
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Consequences of this choice
    consequences: Dict[str, Any] = field(default_factory=dict)
    
    # Choice metadata
    tags: Set[str] = field(default_factory=set)
    tone: Optional[str] = None  # aggressive, friendly, neutral, etc.


@dataclass
class SimulationResult:
    """Result of dialogue simulation."""
    simulation_id: str
    language_code: str
    personality: PlayerPersonality
    
    # Path taken through dialogue
    path: List[str] = field(default_factory=list)
    choices_made: List[str] = field(default_factory=list)
    
    # Issues found
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metrics
    nodes_visited: int = 0
    unique_nodes_visited: int = 0
    total_duration: float = 0.0
    branches_explored: int = 0
    
    # Coverage
    coverage_percentage: float = 0.0
    unreachable_nodes: List[str] = field(default_factory=list)
    
    # Performance
    start_time: datetime = None
    end_time: datetime = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()


@dataclass
class GameState:
    """Current game state during simulation."""
    variables: Dict[str, Any] = field(default_factory=dict)
    flags: Set[str] = field(default_factory=set)
    inventory: List[str] = field(default_factory=list)
    relationships: Dict[str, int] = field(default_factory=dict)
    
    # Player attributes
    player_gender: str = "neutral"
    player_name: str = "Player"
    player_class: str = "default"
    
    # Current context
    current_location: str = "default"
    current_quest: Optional[str] = None
    time_of_day: str = "day"


class DialogueSimulator:
    """
    AI player that simulates dialogue flows to detect issues.
    Tests different paths, personalities, and edge cases.
    """
    
    def __init__(self, localization_service, config: Dict[str, Any]):
        self.localization = localization_service
        self.config = config
        self.max_depth = config.get('max_dialogue_depth', 100)
        self.loop_detection_threshold = config.get('loop_threshold', 3)
        self.simulation_timeout = config.get('simulation_timeout', 300)  # seconds
    
    async def simulate_dialogue(
        self,
        dialogue_tree: Dict[str, DialogueNode],
        start_node_id: str,
        language_code: str,
        personality: PlayerPersonality = PlayerPersonality.EXPLORER,
        initial_state: Optional[GameState] = None
    ) -> SimulationResult:
        """
        Simulate a dialogue flow with AI player.
        
        Args:
            dialogue_tree: Complete dialogue tree structure
            start_node_id: Starting node
            language_code: Language to test
            personality: AI player personality
            initial_state: Initial game state
            
        Returns:
            Simulation result with path taken and issues found
        """
        result = SimulationResult(
            simulation_id=self._generate_simulation_id(),
            language_code=language_code,
            personality=personality
        )
        
        # Initialize state
        state = initial_state or GameState()
        visited_nodes = set()
        node_visit_count = defaultdict(int)
        
        try:
            # Run simulation with timeout
            await asyncio.wait_for(
                self._simulate_recursive(
                    dialogue_tree,
                    start_node_id,
                    language_code,
                    personality,
                    state,
                    result,
                    visited_nodes,
                    node_visit_count,
                    depth=0
                ),
                timeout=self.simulation_timeout
            )
            
        except asyncio.TimeoutError:
            result.issues.append({
                'type': DialogueIssueType.TIMING_ISSUE.value,
                'severity': 'high',
                'message': f'Simulation timeout after {self.simulation_timeout}s',
                'node_id': result.path[-1] if result.path else start_node_id
            })
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            result.issues.append({
                'type': 'simulation_error',
                'severity': 'critical',
                'message': str(e)
            })
        
        # Calculate final metrics
        result.end_time = datetime.utcnow()
        result.unique_nodes_visited = len(visited_nodes)
        
        # Calculate coverage
        total_nodes = len(dialogue_tree)
        result.coverage_percentage = (
            len(visited_nodes) / total_nodes * 100 if total_nodes > 0 else 0
        )
        
        # Find unreachable nodes
        result.unreachable_nodes = [
            node_id for node_id in dialogue_tree.keys()
            if node_id not in visited_nodes
        ]
        
        return result
    
    async def _simulate_recursive(
        self,
        dialogue_tree: Dict[str, DialogueNode],
        current_node_id: str,
        language_code: str,
        personality: PlayerPersonality,
        state: GameState,
        result: SimulationResult,
        visited_nodes: Set[str],
        node_visit_count: Dict[str, int],
        depth: int
    ):
        """Recursive dialogue simulation."""
        # Check depth limit
        if depth > self.max_depth:
            result.issues.append({
                'type': DialogueIssueType.DEAD_END.value,
                'severity': 'medium',
                'message': f'Max depth {self.max_depth} reached',
                'node_id': current_node_id,
                'path': result.path[-10:]  # Last 10 nodes
            })
            return
        
        # Check for loops
        node_visit_count[current_node_id] += 1
        if node_visit_count[current_node_id] > self.loop_detection_threshold:
            result.issues.append({
                'type': DialogueIssueType.INFINITE_LOOP.value,
                'severity': 'high',
                'message': f'Node visited {node_visit_count[current_node_id]} times',
                'node_id': current_node_id,
                'path': result.path[-10:]
            })
            return
        
        # Get current node
        if current_node_id not in dialogue_tree:
            result.issues.append({
                'type': DialogueIssueType.BROKEN_BRANCH.value,
                'severity': 'critical',
                'message': f'Node {current_node_id} not found in tree',
                'previous_node': result.path[-1] if result.path else 'start'
            })
            return
        
        node = dialogue_tree[current_node_id]
        
        # Check node conditions
        if not self._check_conditions(node.conditions, state):
            result.issues.append({
                'type': DialogueIssueType.CONTEXT_ERROR.value,
                'severity': 'medium',
                'message': 'Node conditions not met',
                'node_id': current_node_id,
                'conditions': node.conditions,
                'state': self._serialize_state(state)
            })
            return
        
        # Record visit
        result.path.append(current_node_id)
        result.nodes_visited += 1
        visited_nodes.add(current_node_id)
        
        # Get and validate text
        text = await self._get_localized_text(
            node.localization_key,
            language_code,
            state,
            result
        )
        
        # Check for issues in text
        await self._check_text_issues(
            text, node, language_code, state, result
        )
        
        # Update duration
        if node.audio_duration:
            result.total_duration += node.audio_duration
        
        # Apply state changes
        self._apply_state_changes(node.state_changes, state)
        
        # Terminal node check
        if node.is_terminal or not node.choices:
            return
        
        # Get available choices
        available_choices = [
            choice for choice in node.choices
            if self._check_conditions(choice.conditions, state)
        ]
        
        if not available_choices:
            result.issues.append({
                'type': DialogueIssueType.DEAD_END.value,
                'severity': 'high',
                'message': 'No available choices',
                'node_id': current_node_id,
                'all_choices': len(node.choices),
                'state': self._serialize_state(state)
            })
            return
        
        # Make choice based on personality
        if personality == PlayerPersonality.EXPLORER:
            # Try all branches
            for choice in available_choices:
                # Create state copy for branch
                branch_state = self._copy_state(state)
                
                # Record choice
                result.choices_made.append(choice.choice_id)
                result.branches_explored += 1
                
                # Apply consequences
                self._apply_state_changes(choice.consequences, branch_state)
                
                # Continue simulation
                await self._simulate_recursive(
                    dialogue_tree,
                    choice.target_node_id,
                    language_code,
                    personality,
                    branch_state,
                    result,
                    visited_nodes,
                    node_visit_count.copy(),
                    depth + 1
                )
                
        else:
            # Select single choice based on personality
            choice = self._select_choice(available_choices, personality, state)
            
            # Record choice
            result.choices_made.append(choice.choice_id)
            
            # Apply consequences
            self._apply_state_changes(choice.consequences, state)
            
            # Continue simulation
            await self._simulate_recursive(
                dialogue_tree,
                choice.target_node_id,
                language_code,
                personality,
                state,
                result,
                visited_nodes,
                node_visit_count,
                depth + 1
            )
    
    def _select_choice(
        self,
        choices: List[DialogueChoice],
        personality: PlayerPersonality,
        state: GameState
    ) -> DialogueChoice:
        """Select choice based on personality."""
        if personality == PlayerPersonality.RANDOM:
            return random.choice(choices)
        
        elif personality == PlayerPersonality.SPEEDRUNNER:
            # Prefer choices that advance main quest
            quest_choices = [c for c in choices if 'quest_advance' in c.tags]
            if quest_choices:
                return quest_choices[0]
            
            # Otherwise pick first
            return choices[0]
        
        elif personality == PlayerPersonality.COMPLETIONIST:
            # Prefer choices that give rewards or unlock content
            reward_choices = [c for c in choices if 'reward' in c.tags or 'unlock' in c.tags]
            if reward_choices:
                return reward_choices[0]
            
            # Otherwise pick longest path
            return max(choices, key=lambda c: len(c.localization_key))
        
        elif personality == PlayerPersonality.EVIL:
            # Prefer aggressive/evil choices
            evil_choices = [c for c in choices if c.tone in ['aggressive', 'evil', 'cruel']]
            if evil_choices:
                return evil_choices[0]
            
            # Look for negative consequences
            negative_choices = [
                c for c in choices
                if any(k.startswith('relationship_') and v < 0
                      for k, v in c.consequences.items())
            ]
            if negative_choices:
                return negative_choices[0]
            
            return random.choice(choices)
        
        elif personality == PlayerPersonality.GOOD:
            # Prefer friendly/good choices
            good_choices = [c for c in choices if c.tone in ['friendly', 'good', 'kind']]
            if good_choices:
                return good_choices[0]
            
            # Look for positive consequences
            positive_choices = [
                c for c in choices
                if any(k.startswith('relationship_') and v > 0
                      for k, v in c.consequences.items())
            ]
            if positive_choices:
                return positive_choices[0]
            
            return random.choice(choices)
        
        elif personality == PlayerPersonality.CHAOTIC:
            # Alternate between extremes
            if random.random() < 0.5:
                # Try evil choice
                evil_choices = [c for c in choices if c.tone in ['aggressive', 'evil']]
                if evil_choices:
                    return random.choice(evil_choices)
            else:
                # Try good choice
                good_choices = [c for c in choices if c.tone in ['friendly', 'good']]
                if good_choices:
                    return random.choice(good_choices)
            
            # Otherwise random
            return random.choice(choices)
        
        # Default to first choice
        return choices[0]
    
    async def _get_localized_text(
        self,
        key: str,
        language_code: str,
        state: GameState,
        result: SimulationResult
    ) -> str:
        """Get localized text and check for issues."""
        try:
            # Build context from game state
            context = {
                'player_name': state.player_name,
                'player_gender': state.player_gender,
                'player_class': state.player_class,
                **state.variables
            }
            
            text = await self.localization.get_string(key, language_code, context)
            
            # Check for missing translation
            if text.startswith('[') and text.endswith(']'):
                result.issues.append({
                    'type': DialogueIssueType.MISSING_TRANSLATION.value,
                    'severity': 'critical',
                    'key': key,
                    'language': language_code
                })
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to get localized text for {key}: {e}")
            result.issues.append({
                'type': 'localization_error',
                'severity': 'critical',
                'key': key,
                'error': str(e)
            })
            return f"[ERROR: {key}]"
    
    async def _check_text_issues(
        self,
        text: str,
        node: DialogueNode,
        language_code: str,
        state: GameState,
        result: SimulationResult
    ):
        """Check for various issues in localized text."""
        # Check for variable placeholders
        placeholders = re.findall(r'\{(\w+)\}', text)
        for placeholder in placeholders:
            if placeholder not in state.variables and placeholder not in [
                'player_name', 'player_gender', 'player_class'
            ]:
                result.issues.append({
                    'type': DialogueIssueType.VARIABLE_ERROR.value,
                    'severity': 'high',
                    'node_id': node.node_id,
                    'variable': placeholder,
                    'text': text
                })
        
        # Check for gender consistency
        if state.player_gender != 'neutral':
            gender_markers = self._get_gender_markers(language_code)
            inconsistencies = self._check_gender_consistency(
                text, state.player_gender, gender_markers
            )
            
            if inconsistencies:
                result.issues.append({
                    'type': DialogueIssueType.GENDER_MISMATCH.value,
                    'severity': 'medium',
                    'node_id': node.node_id,
                    'expected_gender': state.player_gender,
                    'issues': inconsistencies
                })
        
        # Check for cultural issues
        cultural_issues = await self._check_cultural_appropriateness(
            text, language_code, node.tags
        )
        
        if cultural_issues:
            result.issues.append({
                'type': DialogueIssueType.CULTURAL_ISSUE.value,
                'severity': 'high',
                'node_id': node.node_id,
                'issues': cultural_issues
            })
    
    def _check_conditions(self, conditions: Dict[str, Any], state: GameState) -> bool:
        """Check if conditions are met."""
        for key, expected in conditions.items():
            if key.startswith('flag_'):
                # Check flag
                flag_name = key[5:]
                if isinstance(expected, bool):
                    if (flag_name in state.flags) != expected:
                        return False
                        
            elif key.startswith('var_'):
                # Check variable
                var_name = key[4:]
                if var_name not in state.variables:
                    return False
                    
                actual = state.variables[var_name]
                
                # Handle different comparison types
                if isinstance(expected, dict):
                    op = expected.get('op', '==')
                    value = expected.get('value')
                    
                    if op == '>' and actual <= value:
                        return False
                    elif op == '<' and actual >= value:
                        return False
                    elif op == '>=' and actual < value:
                        return False
                    elif op == '<=' and actual > value:
                        return False
                    elif op == '==' and actual != value:
                        return False
                    elif op == '!=' and actual == value:
                        return False
                else:
                    if actual != expected:
                        return False
                        
            elif key.startswith('item_'):
                # Check inventory
                item_name = key[5:]
                if isinstance(expected, bool):
                    if (item_name in state.inventory) != expected:
                        return False
        
        return True
    
    def _apply_state_changes(self, changes: Dict[str, Any], state: GameState):
        """Apply state changes."""
        for key, value in changes.items():
            if key.startswith('flag_'):
                # Set/unset flag
                flag_name = key[5:]
                if value:
                    state.flags.add(flag_name)
                else:
                    state.flags.discard(flag_name)
                    
            elif key.startswith('var_'):
                # Set variable
                var_name = key[4:]
                if isinstance(value, dict) and 'op' in value:
                    # Relative change
                    op = value['op']
                    amount = value.get('value', 0)
                    current = state.variables.get(var_name, 0)
                    
                    if op == '+':
                        state.variables[var_name] = current + amount
                    elif op == '-':
                        state.variables[var_name] = current - amount
                    elif op == '*':
                        state.variables[var_name] = current * amount
                else:
                    # Absolute change
                    state.variables[var_name] = value
                    
            elif key.startswith('item_'):
                # Add/remove item
                item_name = key[5:]
                if value:
                    if item_name not in state.inventory:
                        state.inventory.append(item_name)
                else:
                    if item_name in state.inventory:
                        state.inventory.remove(item_name)
                        
            elif key.startswith('relationship_'):
                # Change relationship
                character = key[13:]
                if isinstance(value, int):
                    # Absolute value
                    state.relationships[character] = value
                elif isinstance(value, dict) and 'change' in value:
                    # Relative change
                    current = state.relationships.get(character, 0)
                    state.relationships[character] = current + value['change']
    
    def _copy_state(self, state: GameState) -> GameState:
        """Create a deep copy of game state."""
        return GameState(
            variables=state.variables.copy(),
            flags=state.flags.copy(),
            inventory=state.inventory.copy(),
            relationships=state.relationships.copy(),
            player_gender=state.player_gender,
            player_name=state.player_name,
            player_class=state.player_class,
            current_location=state.current_location,
            current_quest=state.current_quest,
            time_of_day=state.time_of_day
        )
    
    def _serialize_state(self, state: GameState) -> Dict[str, Any]:
        """Serialize game state for logging."""
        return {
            'variables': state.variables,
            'flags': list(state.flags),
            'inventory': state.inventory,
            'relationships': state.relationships
        }
    
    def _get_gender_markers(self, language_code: str) -> Dict[str, List[str]]:
        """Get gender-specific markers for language."""
        # Simplified gender markers - in production would be more comprehensive
        markers = {
            'en-US': {
                'masculine': ['he', 'him', 'his'],
                'feminine': ['she', 'her', 'hers'],
                'neutral': ['they', 'them', 'their']
            },
            'fr-FR': {
                'masculine': ['il', 'lui', 'son', 'le'],
                'feminine': ['elle', 'la', 'sa'],
                'neutral': ['iel', 'ellui']  # Neo-pronouns
            },
            'es-ES': {
                'masculine': ['él', 'lo', 'su'],
                'feminine': ['ella', 'la', 'su'],
                'neutral': ['elle', 'le']
            }
            # Add more languages...
        }
        
        return markers.get(language_code, markers['en-US'])
    
    def _check_gender_consistency(
        self,
        text: str,
        expected_gender: str,
        markers: Dict[str, List[str]]
    ) -> List[str]:
        """Check for gender consistency in text."""
        issues = []
        text_lower = text.lower()
        
        # Check for conflicting gender markers
        for gender, gender_markers in markers.items():
            if gender != expected_gender:
                for marker in gender_markers:
                    if f' {marker} ' in f' {text_lower} ':
                        issues.append(
                            f"Found {gender} marker '{marker}' but expected {expected_gender}"
                        )
        
        return issues
    
    async def _check_cultural_appropriateness(
        self,
        text: str,
        language_code: str,
        tags: Set[str]
    ) -> List[str]:
        """Check for cultural appropriateness issues."""
        issues = []
        
        # This would be much more sophisticated in production
        # Could integrate with cultural sensitivity APIs
        
        # Example checks
        if language_code == 'ja-JP':
            # Check for inappropriate casualness
            if 'formal' in tags and any(marker in text for marker in ['だよ', 'じゃん']):
                issues.append("Casual speech markers in formal context")
                
        elif language_code == 'ar-SA':
            # Check for religious sensitivity
            if any(term in text.lower() for term in ['alcohol', 'pork']):
                if 'culturally_sensitive' not in tags:
                    issues.append("Potentially sensitive content for target culture")
        
        return issues
    
    def _generate_simulation_id(self) -> str:
        """Generate unique simulation ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    async def simulate_all_personalities(
        self,
        dialogue_tree: Dict[str, DialogueNode],
        start_node_id: str,
        language_code: str,
        initial_state: Optional[GameState] = None
    ) -> Dict[PlayerPersonality, SimulationResult]:
        """Run simulation with all personality types."""
        results = {}
        
        for personality in PlayerPersonality:
            logger.info(f"Simulating with {personality} personality")
            
            result = await self.simulate_dialogue(
                dialogue_tree,
                start_node_id,
                language_code,
                personality,
                initial_state
            )
            
            results[personality] = result
        
        return results
    
    async def generate_coverage_report(
        self,
        results: Dict[PlayerPersonality, SimulationResult]
    ) -> Dict[str, Any]:
        """Generate coverage report from multiple simulations."""
        # Combine coverage from all simulations
        all_visited_nodes = set()
        all_issues = []
        
        for personality, result in results.items():
            all_visited_nodes.update(result.path)
            all_issues.extend(result.issues)
        
        # De-duplicate issues
        unique_issues = []
        seen_issues = set()
        
        for issue in all_issues:
            issue_key = (
                issue.get('type', ''),
                issue.get('node_id', ''),
                issue.get('key', '')
            )
            if issue_key not in seen_issues:
                seen_issues.add(issue_key)
                unique_issues.append(issue)
        
        # Group issues by type
        issues_by_type = defaultdict(list)
        for issue in unique_issues:
            issue_type = issue.get('type', 'unknown')
            issues_by_type[issue_type].append(issue)
        
        # Calculate aggregate metrics
        total_nodes = max(
            len(set(r.path)) for r in results.values()
        ) if results else 0
        
        report = {
            'total_simulations': len(results),
            'personalities_tested': [p.value for p in results.keys()],
            'aggregate_coverage': {
                'total_unique_nodes': len(all_visited_nodes),
                'max_possible_nodes': total_nodes,
                'coverage_percentage': (
                    len(all_visited_nodes) / total_nodes * 100
                    if total_nodes > 0 else 0
                )
            },
            'issues_summary': {
                'total_issues': len(unique_issues),
                'by_type': {
                    issue_type: len(issues)
                    for issue_type, issues in issues_by_type.items()
                },
                'critical_issues': [
                    issue for issue in unique_issues
                    if issue.get('severity') == 'critical'
                ]
            },
            'personality_metrics': {
                personality.value: {
                    'nodes_visited': result.nodes_visited,
                    'branches_explored': result.branches_explored,
                    'issues_found': len(result.issues),
                    'coverage': result.coverage_percentage
                }
                for personality, result in results.items()
            }
        }
        
        return report


# Utility functions for dialogue tree construction
def build_dialogue_tree_from_json(json_data: Dict[str, Any]) -> Dict[str, DialogueNode]:
    """Build dialogue tree from JSON representation."""
    tree = {}
    
    for node_data in json_data.get('nodes', []):
        node = DialogueNode(
            node_id=node_data['id'],
            speaker_id=node_data.get('speaker', 'narrator'),
            localization_key=node_data['text_key'],
            conditions=node_data.get('conditions', {}),
            state_changes=node_data.get('state_changes', {}),
            tags=set(node_data.get('tags', [])),
            audio_duration=node_data.get('audio_duration'),
            is_terminal=node_data.get('is_terminal', False)
        )
        
        # Build choices
        for choice_data in node_data.get('choices', []):
            choice = DialogueChoice(
                choice_id=choice_data['id'],
                localization_key=choice_data['text_key'],
                target_node_id=choice_data['target'],
                conditions=choice_data.get('conditions', {}),
                consequences=choice_data.get('consequences', {}),
                tags=set(choice_data.get('tags', [])),
                tone=choice_data.get('tone')
            )
            node.choices.append(choice)
        
        tree[node.node_id] = node
    
    return tree


def validate_dialogue_tree(tree: Dict[str, DialogueNode]) -> List[str]:
    """Validate dialogue tree structure."""
    errors = []
    
    # Check all target nodes exist
    for node_id, node in tree.items():
        for choice in node.choices:
            if choice.target_node_id not in tree:
                errors.append(
                    f"Node {node_id} choice {choice.choice_id} targets "
                    f"non-existent node {choice.target_node_id}"
                )
    
    # Check for orphaned nodes (no incoming edges except start nodes)
    incoming_edges = defaultdict(list)
    for node_id, node in tree.items():
        for choice in node.choices:
            incoming_edges[choice.target_node_id].append(node_id)
    
    for node_id in tree.keys():
        if node_id not in incoming_edges and 'start' not in node_id.lower():
            errors.append(f"Node {node_id} has no incoming edges (orphaned)")
    
    return errors


from collections import defaultdict
