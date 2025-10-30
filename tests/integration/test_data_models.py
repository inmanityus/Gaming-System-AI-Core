"""
REAL integration tests for data models.
Tests actual PostgreSQL connection, migrations, and CRUD operations.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.player import Player
from models.game_state import GameState
from models.story_node import StoryNode
from models.transaction import Transaction
from models.world_state import WorldState
from models.npc import NPC
from models.faction import Faction
from models.augmentation import Augmentation
from models.base import Base

# Database connection from environment or defaults
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5443")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", os.getenv("PGPASSWORD", "Inn0vat1on!"))

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@pytest.fixture(scope="module")
def engine():
    """Create database engine for testing."""
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Create test database schema
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup: Drop all tables after tests
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    """Create database session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Rollback any changes
    session.rollback()
    session.close()


def test_database_connection(engine):
    """Test that we can connect to PostgreSQL."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        assert "PostgreSQL" in version
        print(f"✓ Connected to PostgreSQL: {version[:50]}...")


def test_player_create_and_read(session):
    """Test creating and reading a Player record."""
    # Create player
    player = Player(
        steam_id="STEAM_1234567890",
        username="TestPlayer",
        tier="free",
        stats={"health": 100, "strength": 50, "speed": 30},
        inventory=[{"item_id": "sword", "quantity": 1}],
        money=Decimal("1000.50"),
        reputation=10,
        level=5,
        xp=Decimal("2500.0")
    )
    
    session.add(player)
    session.commit()
    
    # Read player
    retrieved = session.query(Player).filter_by(steam_id="STEAM_1234567890").first()
    
    assert retrieved is not None
    assert retrieved.username == "TestPlayer"
    assert retrieved.tier == "free"
    assert retrieved.stats["health"] == 100
    assert float(retrieved.money) == 1000.50
    assert retrieved.level == 5
    
    # Test JSON serialization
    player_dict = retrieved.to_dict()
    assert player_dict["username"] == "TestPlayer"
    assert player_dict["steam_id"] == "STEAM_1234567890"
    
    print("✓ Player create and read test passed")


def test_game_state_create_and_read(session):
    """Test creating and reading a GameState record."""
    # First create a player
    player = Player(
        steam_id="STEAM_GAMESTATE_TEST",
        username="GameStateTest",
        tier="premium"
    )
    session.add(player)
    session.commit()
    
    # Create game state
    game_state = GameState(
        player_id=player.id,
        current_world="night",
        location="warehouse_district",
        position={"x": 100.5, "y": 200.3, "z": 50.0},
        active_quests=["quest_001", "quest_002"],
        session_data={"last_played": "2025-01-29"},
        is_active=True
    )
    
    session.add(game_state)
    session.commit()
    
    # Read game state
    retrieved = session.query(GameState).filter_by(player_id=player.id).first()
    
    assert retrieved is not None
    assert retrieved.current_world == "night"
    assert retrieved.position["x"] == 100.5
    assert retrieved.active_quests == ["quest_001", "quest_002"]
    
    print("✓ GameState create and read test passed")


def test_story_node_create_and_read(session):
    """Test creating and reading a StoryNode record."""
    # Create player
    player = Player(steam_id="STEAM_STORY_TEST", username="StoryTest", tier="free")
    session.add(player)
    session.commit()
    
    # Create story node
    story_node = StoryNode(
        player_id=player.id,
        node_type="quest",
        title="The First Deal",
        description="A dangerous trade with vampires",
        narrative_content="You approach the dark warehouse...",
        choices=[
            {"choice_id": "accept", "text": "Accept the deal", "leads_to": "node_002"},
            {"choice_id": "refuse", "text": "Walk away", "leads_to": "node_003"}
        ],
        status="active",
        prerequisites=[],
        consequences={"money": 500, "reputation": -10}
    )
    
    session.add(story_node)
    session.commit()
    
    # Read story node
    retrieved = session.query(StoryNode).filter_by(player_id=player.id).first()
    
    assert retrieved is not None
    assert retrieved.title == "The First Deal"
    assert retrieved.node_type == "quest"
    assert len(retrieved.choices) == 2
    
    print("✓ StoryNode create and read test passed")


def test_transaction_create_and_read(session):
    """Test creating and reading a Transaction record."""
    # Create player
    player = Player(steam_id="STEAM_TRANS_TEST", username="TransactionTest", tier="premium")
    session.add(player)
    session.commit()
    
    # Create transaction
    transaction = Transaction(
        player_id=player.id,
        transaction_type="payment",
        stripe_payment_intent_id="pi_test_123456",
        amount=Decimal("29.99"),
        currency="USD",
        status="completed",
        description="Premium subscription",
        metadata={"subscription_tier": "premium", "billing_period": "monthly"}
    )
    
    session.add(transaction)
    session.commit()
    
    # Read transaction
    retrieved = session.query(Transaction).filter_by(stripe_payment_intent_id="pi_test_123456").first()
    
    assert retrieved is not None
    assert retrieved.transaction_type == "payment"
    assert float(retrieved.amount) == 29.99
    assert retrieved.status == "completed"
    
    print("✓ Transaction create and read test passed")


def test_world_state_create_and_read(session):
    """Test creating and reading a WorldState record."""
    # Create world state
    world_state = WorldState(
        world_time=datetime.utcnow(),
        day_phase="night",
        weather="fog",
        faction_power={
            "vampire_house_alpha": {"power": 85, "influence": 90},
            "werewolf_pack_beta": {"power": 70, "influence": 75}
        },
        global_events=[
            {"event_id": "evt_001", "type": "territory_shift", "description": "Vampires expand territory"}
        ],
        economic_state={"body_parts_price": 500, "equipment_price": 1000},
        npc_population={"vampire": 15, "werewolf": 10, "human": 50}
    )
    
    session.add(world_state)
    session.commit()
    
    # Read world state
    retrieved = session.query(WorldState).filter_by(day_phase="night").first()
    
    assert retrieved is not None
    assert retrieved.weather == "fog"
    assert retrieved.faction_power["vampire_house_alpha"]["power"] == 85
    assert retrieved.npc_population["vampire"] == 15
    
    print("✓ WorldState create and read test passed")


def test_faction_create_and_read(session):
    """Test creating and reading a Faction record."""
    # Create faction
    faction = Faction(
        name="House of Crimson Shadows",
        faction_type="vampire_house",
        description="An ancient vampire house with dark secrets",
        power_level=85,
        territory=[
            {"territory_id": "downtown", "control_level": 90},
            {"territory_id": "warehouse_district", "control_level": 75}
        ],
        relationships={
            "faction_werewolf_pack": {"relationship_type": "enemy", "strength": -80}
        },
        hierarchy={
            "lord": {"member_id": "npc_001", "power_level": 100},
            "enforcer": {"member_id": "npc_002", "power_level": 80}
        },
        goals=[{"goal_id": "expand_territory", "priority": 1, "progress": 50}]
    )
    
    session.add(faction)
    session.commit()
    
    # Read faction
    retrieved = session.query(Faction).filter_by(name="House of Crimson Shadows").first()
    
    assert retrieved is not None
    assert retrieved.faction_type == "vampire_house"
    assert retrieved.power_level == 85
    assert len(retrieved.territory) == 2
    
    print("✓ Faction create and read test passed")


def test_npc_create_and_read(session):
    """Test creating and reading an NPC record."""
    # Create world state and faction first
    world_state = WorldState(day_phase="night")
    session.add(world_state)
    session.flush()
    
    faction = Faction(name="Test Faction", faction_type="vampire_house")
    session.add(faction)
    session.flush()
    
    # Create NPC with 50-dimensional personality vector
    personality_vector = [0.5 + (i * 0.01) for i in range(50)]  # 50 dimensions
    
    npc = NPC(
        world_state_id=world_state.id,
        faction_id=faction.id,
        name="Marcus the Ancient",
        npc_type="vampire",
        personality_vector=personality_vector,
        stats={"health": 200, "aggression": 75, "intelligence": 90, "charisma": 85},
        goal_stack=[{"goal_id": "expand_power", "priority": 1, "status": "active"}],
        current_location="mansion_district",
        current_state="idle",
        relationships={"player_001": {"relationship_type": "neutral", "score": 50}}
    )
    
    session.add(npc)
    session.commit()
    
    # Read NPC
    retrieved = session.query(NPC).filter_by(name="Marcus the Ancient").first()
    
    assert retrieved is not None
    assert retrieved.npc_type == "vampire"
    assert len(retrieved.personality_vector) == 50
    assert retrieved.faction_id == faction.id
    
    print("✓ NPC create and read test passed")


def test_augmentation_create_and_read(session):
    """Test creating and reading an Augmentation record."""
    # Create augmentation
    augmentation = Augmentation(
        name="Invisibility",
        description="The ability to become invisible to enemies",
        category="power",
        cost=Decimal("5000.00"),
        stats_modifier={"invisibility": True, "stealth": 50},
        requirements={"level": 10, "quest_unlock": "quest_005"}
    )
    
    session.add(augmentation)
    session.commit()
    
    # Read augmentation
    retrieved = session.query(Augmentation).filter_by(name="Invisibility").first()
    
    assert retrieved is not None
    assert retrieved.category == "power"
    assert float(retrieved.cost) == 5000.00
    assert retrieved.stats_modifier["invisibility"] is True
    
    print("✓ Augmentation create and read test passed")


def test_foreign_key_relationships(session):
    """Test that foreign key relationships work correctly."""
    # Create player
    player = Player(steam_id="STEAM_FK_TEST", username="FKTest", tier="free")
    session.add(player)
    session.commit()
    
    # Create game state linked to player
    game_state = GameState(player_id=player.id, current_world="day")
    session.add(game_state)
    session.commit()
    
    # Verify relationship
    assert game_state.player_id == player.id
    assert game_state.player.username == "FKTest"
    
    # Test cascade delete (player deletion should delete game state)
    session.delete(player)
    session.commit()
    
    # Verify game state was deleted
    deleted_state = session.query(GameState).filter_by(id=game_state.id).first()
    assert deleted_state is None
    
    print("✓ Foreign key relationships test passed")


def test_json_serialization(session):
    """Test that all models support JSON serialization."""
    # Create sample records
    player = Player(steam_id="STEAM_JSON_TEST", username="JSONTest", tier="premium")
    session.add(player)
    session.commit()
    
    game_state = GameState(player_id=player.id, current_world="day")
    session.add(game_state)
    session.commit()
    
    # Test JSON serialization
    player_json = player.to_json()
    assert "JSONTest" in player_json
    assert "premium" in player_json
    
    game_state_json = game_state.to_json()
    assert "day" in game_state_json
    
    print("✓ JSON serialization test passed")


if __name__ == "__main__":
    # Run tests directly (for manual testing)
    pytest.main([__file__, "-v", "-s"])

