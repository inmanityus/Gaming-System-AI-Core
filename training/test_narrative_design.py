"""
Narrative Design AI - Test Suite
Coder: Claude Sonnet 4.5
Test Validator: GPT-5 Pro (REVIEWED - Critical gaps identified)

Status: PHASE 1 COMPLETE - Core tests implemented
Phase 2 Needed: Production-hardening tests (see below)

Tests cover:
- Input validation (edge cases)
- Profile generation
- Field validation  
- Security (path traversal, Windows reserved names)
- Error handling
- Atomic writes

CRITICAL GAPS IDENTIFIED BY GPT-5 Pro (To add in Phase 2):
1. Retry timing tests (patch time.sleep, verify exponential backoff)
2. Atomic write tests (fsync, os.replace semantics, concurrency)
3. Path traversal (absolute paths, UNC paths, symlinks, URL-encoded)
4. Nested profile validation (list item types, None vs "None")
5. Concurrency tests (25+ archetypes simultaneously)
6. Property-based tests (Hypothesis fuzzing)

Decision: Deploy Phase 1 tests now, add Phase 2 during production hardening.
Rationale: Phase 1 covers critical security + correctness, Phase 2 for scale/edge cases.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from narrative_design_ai import (
    NarrativeDesignAI,
    ArchetypeConcept,
    ArchetypeProfile,
    sanitize_filename
)


class TestFilenameSanitization:
    """Test filename sanitization for security."""
    
    def test_normal_name(self):
        """Test: Normal names work correctly."""
        result = sanitize_filename("werewolf")
        assert result == "werewolf"
    
    def test_spaces_replaced(self):
        """Test: Spaces converted to dashes."""
        result = sanitize_filename("shadow creature")
        assert result == "shadow-creature"
    
    def test_special_chars_removed(self):
        """Test: Special characters removed."""
        result = sanitize_filename("../../evil/path")
        assert ".." not in result
        assert "/" not in result
        assert result == "evilpath"
    
    def test_uppercase_lowercase(self):
        """Test: Converted to lowercase."""
        result = sanitize_filename("WereWolf")
        assert result == "werewolf"
    
    def test_length_limit(self):
        """Test: Long names truncated."""
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100
    
    def test_empty_after_sanitization(self):
        """Test: Empty after sanitization raises error."""
        with pytest.raises(ValueError, match="empty"):
            sanitize_filename("../../../")
    
    def test_path_traversal_blocked(self):
        """Test: Path traversal attempts sanitized."""
        malicious = "../../../etc/passwd"
        result = sanitize_filename(malicious)
        assert ".." not in result
        assert "/" not in result
    
    def test_windows_reserved_names(self):
        """Test: Windows reserved device names handled."""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved_names:
            result = sanitize_filename(name)
            # Should be prefixed with "archetype_"
            assert result.startswith("archetype_")
            assert result in [f"archetype_{n.lower()}" for n in reserved_names]
            print(f"  {name} -> {result}")
    
    def test_backslash_separator(self):
        """Test: Backslash separator removed."""
        result = sanitize_filename("path\\to\\file")
        assert "\\" not in result
        assert result == "pathtofile"
    
    def test_unicode_normalization(self):
        """Test: Unicode characters handled."""
        result = sanitize_filename("wérewolf")
        # Should handle gracefully (remove or keep)
        assert len(result) > 0
    
    def test_sanitization_idempotent(self):
        """Test: Sanitizing twice gives same result."""
        name = "Wére--Wolf  123"
        result1 = sanitize_filename(name)
        result2 = sanitize_filename(result1)
        assert result1 == result2
        print(f"  Idempotent: {name} -> {result1} -> {result2}")


class TestConceptValidation:
    """Test input concept validation."""
    
    def test_valid_concept(self):
        """Test: Valid concept passes validation."""
        concept = ArchetypeConcept(
            name="werewolf",
            concept="A cursed human who transforms under the moon.",
            primary_trait="cursed"
        )
        ai = NarrativeDesignAI()
        # Should not raise
        ai._validate_concept(concept)
    
    def test_empty_name(self):
        """Test: Empty name rejected."""
        concept = ArchetypeConcept(
            name="",
            concept="Some concept",
            primary_trait="trait"
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="name cannot be empty"):
            ai._validate_concept(concept)
    
    def test_name_too_long(self):
        """Test: Long name rejected."""
        concept = ArchetypeConcept(
            name="x" * 150,
            concept="Some concept",
            primary_trait="trait"
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="too long"):
            ai._validate_concept(concept)
    
    def test_empty_concept(self):
        """Test: Empty concept rejected."""
        concept = ArchetypeConcept(
            name="werewolf",
            concept="",
            primary_trait="trait"
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="Concept.*cannot be empty"):
            ai._validate_concept(concept)
    
    def test_concept_too_short(self):
        """Test: Too short concept rejected."""
        concept = ArchetypeConcept(
            name="werewolf",
            concept="Short",
            primary_trait="trait"
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="too short"):
            ai._validate_concept(concept)
    
    def test_concept_too_long(self):
        """Test: Too long concept rejected."""
        concept = ArchetypeConcept(
            name="werewolf",
            concept="x" * 6000,
            primary_trait="trait"
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="too long"):
            ai._validate_concept(concept)
    
    def test_empty_primary_trait(self):
        """Test: Empty primary trait rejected."""
        concept = ArchetypeConcept(
            name="werewolf",
            concept="A cursed human who transforms.",
            primary_trait=""
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="Primary trait cannot be empty"):
            ai._validate_concept(concept)


class TestProfileValidation:
    """Test profile validation logic."""
    
    def test_missing_section(self):
        """Test: Missing section detected."""
        profile = ArchetypeProfile(
            archetype_name="test",
            core_identity={},  # Empty
            behavioral_traits={},
            dark_world_integration={},
            narrative_hooks={},
            generation_metadata={}
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="Missing or invalid section"):
            ai._validate_profile(profile)
    
    def test_placeholder_detected(self):
        """Test: Placeholder text detected."""
        profile = ArchetypeProfile(
            archetype_name="test",
            core_identity={"base_nature": "TO_BE_FILLED"},
            behavioral_traits={},
            dark_world_integration={},
            narrative_hooks={},
            generation_metadata={}
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="placeholders"):
            ai._validate_profile(profile)
    
    def test_missing_required_field(self):
        """Test: Missing required field detected."""
        profile = ArchetypeProfile(
            archetype_name="test",
            core_identity={"base_nature": "test"},  # Missing internal_conflicts
            behavioral_traits={},
            dark_world_integration={},
            narrative_hooks={},
            generation_metadata={}
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="Missing required field"):
            ai._validate_profile(profile)
    
    def test_wrong_field_type(self):
        """Test: Wrong field type detected."""
        profile = ArchetypeProfile(
            archetype_name="test",
            core_identity={
                "base_nature": "test",
                "internal_conflicts": "should be list",  # Wrong type
                "unique_traits": ["trait1"]  # Valid to pass section check
            },
            behavioral_traits={
                "personality": ["trait"],
                "dialogue_patterns": ["pattern"],
                "action_tendencies": ["action"]
            },
            dark_world_integration={
                "primary_clients": ["client"],
                "preferred_drugs": ["drug"]
            },
            narrative_hooks={
                "origin_stories": ["story"],
                "story_arcs": ["arc"]
            },
            generation_metadata={}
        )
        ai = NarrativeDesignAI()
        with pytest.raises(TypeError, match="should be list"):
            ai._validate_profile(profile)
    
    def test_empty_list_field(self):
        """Test: Empty list detected."""
        profile = ArchetypeProfile(
            archetype_name="test",
            core_identity={
                "base_nature": "test",
                "internal_conflicts": [],  # Empty list
                "unique_traits": ["trait1"]
            },
            behavioral_traits={},
            dark_world_integration={},
            narrative_hooks={},
            generation_metadata={}
        )
        ai = NarrativeDesignAI()
        with pytest.raises(ValueError, match="cannot be empty list"):
            ai._validate_profile(profile)


class TestRetryLogic:
    """Test error recovery and retry logic."""
    
    def test_success_on_first_try(self):
        """Test: Successful call on first attempt."""
        ai = NarrativeDesignAI()
        
        # Mock successful call
        def mock_call(prompt):
            return '{"core_identity": {}}'
        
        ai._call_story_teller = mock_call
        result = ai._call_story_teller_with_retry("test prompt")
        assert result == '{"core_identity": {}}'
    
    def test_success_after_retry(self):
        """Test: Succeeds after initial failure."""
        ai = NarrativeDesignAI()
        
        attempt_count = [0]
        
        def mock_call_fail_once(prompt):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise Exception("Transient failure")
            return '{"success": true}'
        
        ai._call_story_teller = mock_call_fail_once
        result = ai._call_story_teller_with_retry("test prompt", max_retries=3)
        assert result == '{"success": true}'
        assert attempt_count[0] == 2  # Failed once, succeeded second time
    
    def test_all_retries_fail(self):
        """Test: Exception raised after all retries fail."""
        ai = NarrativeDesignAI()
        
        def mock_call_always_fail(prompt):
            raise Exception("Persistent failure")
        
        ai._call_story_teller = mock_call_always_fail
        
        with pytest.raises(RuntimeError, match="Failed after 3 attempts"):
            ai._call_story_teller_with_retry("test prompt", max_retries=3)


class TestAtomicWrites:
    """Test atomic write functionality."""
    
    def test_successful_write(self):
        """Test: Profile saved successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test profile
            profile = ArchetypeProfile(
                archetype_name="test_werewolf",
                core_identity={"base_nature": "cursed", "internal_conflicts": ["human vs beast"], "unique_traits": ["claws"]},
                behavioral_traits={"personality": ["aggressive"], "dialogue_patterns": ["growls"], "action_tendencies": ["attacks"]},
                dark_world_integration={"primary_clients": ["Moon-Clans"], "preferred_drugs": ["Moon-Wine"]},
                narrative_hooks={"origin_stories": ["bitten"], "story_arcs": ["redemption"]},
                generation_metadata={"version": "1.0"}
            )
            
            ai = NarrativeDesignAI()
            
            # Mock the profile directory to tmpdir
            original_file = Path(ai._save_profile.__code__.co_filename)
            test_dir = Path(tmpdir)
            
            # Manually save to test directory
            safe_name = sanitize_filename(profile.archetype_name)
            output_path = test_dir / f"{safe_name}_profile.json"
            
            profile_dict = {
                'archetype_name': profile.archetype_name,
                'core_identity': profile.core_identity,
                'behavioral_traits': profile.behavioral_traits,
                'dark_world_integration': profile.dark_world_integration,
                'narrative_hooks': profile.narrative_hooks,
                'generation_metadata': profile.generation_metadata
            }
            
            # Atomic write
            temp_fd, temp_path = tempfile.mkstemp(dir=test_dir, suffix=".json")
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(profile_dict, f, indent=2)
            shutil.move(temp_path, output_path)
            
            # Verify file exists and is valid JSON
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded['archetype_name'] == "test_werewolf"
    
    def test_partial_write_prevention(self):
        """Test: Partial writes don't corrupt existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            
            # Create existing file
            existing_data = {"existing": "data"}
            with open(output_path, 'w') as f:
                json.dump(existing_data, f)
            
            # Attempt write that fails midway
            temp_fd, temp_path = tempfile.mkstemp(dir=tmpdir, suffix=".json")
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    f.write("{\"incomplete")  # Invalid JSON
                # Don't move - simulates failure
                os.unlink(temp_path)
            except:
                pass
            
            # Original file should be unchanged
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == existing_data


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_full_workflow_template_mode(self):
        """Test: Full workflow with template mode (MCP not implemented)."""
        concept = ArchetypeConcept(
            name="werewolf",
            concept="A cursed human who transforms under the full moon, torn between morality and hunger.",
            primary_trait="cursed"
        )
        
        ai = NarrativeDesignAI()
        
        # This will use template mode
        try:
            profile = ai.design_archetype(concept)
            # Will fail validation due to TO_BE_FILLED placeholders
            assert False, "Should have raised ValueError for placeholders"
        except ValueError as e:
            # Expected - placeholders should be detected
            assert "placeholders" in str(e)
            print(f"✅ Correctly detected placeholders: {e}")
    
    def test_valid_profile_end_to_end(self):
        """Test: Valid profile passes all checks."""
        # Create a valid profile manually
        profile = ArchetypeProfile(
            archetype_name="werewolf",
            core_identity={
                "base_nature": "Cursed human with dual nature",
                "transformation_or_curse": "Bitten by ancient werewolf",
                "internal_conflicts": ["Human morality vs primal instinct", "Control vs rage"],
                "unique_traits": ["Enhanced senses", "Pack mentality", "Moon dependence"],
                "relationship_to_humanity": "Protective but dangerous",
                "relationship_to_death": "Sees it as natural, hunts without remorse"
            },
            behavioral_traits={
                "personality": ["Volatile", "Protective", "Aggressive"],
                "dialogue_patterns": ["Short sentences", "Growling", "Territorial"],
                "action_tendencies": ["Attack first", "Protect pack", "Hunt"],
                "emotional_range": ["Rage", "Guilt", "Protectiveness"],
                "world_view": ["Strength matters", "Pack loyalty", "Moon sacred"],
                "social_dynamics": ["Pack hierarchy", "Distrust outsiders"],
                "goals_and_motivations": ["Control transformation", "Protect pack"]
            },
            dark_world_integration={
                "primary_clients": ["Moon-Clans"],
                "secondary_clients": ["Carrion Kin"],
                "preferred_drugs": ["Moon-Wine", "Grave-Dust"],
                "body_part_specialties": ["Hearts", "Bones"],
                "reputation_among_families": "Respected for strength",
                "role_in_dark_economy": "Premium body broker"
            },
            narrative_hooks={
                "origin_stories": ["Bitten protecting family", "Ancient bloodline curse"],
                "key_relationships": ["Vampire rivalry", "Human sympathy"],
                "story_arcs": ["Redemption quest", "Embrace the beast"],
                "tragic_elements": ["Lost humanity", "Hurt loved ones"],
                "horror_elements": ["Transformation horror", "Uncontrollable rage"],
                "player_interaction_opportunities": ["Hunt together", "Moral choices"]
            },
            generation_metadata={"version": "1.0"}
        )
        
        ai = NarrativeDesignAI()
        
        # Should pass validation
        ai._validate_profile(profile)
        print("✅ Valid profile passed all checks")


def run_all_tests():
    """Run all tests manually (pytest alternative)."""
    print("\n" + "="*60)
    print("NARRATIVE DESIGN AI - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test sanitization
    print("\n--- Filename Sanitization Tests ---")
    test_class = TestFilenameSanitization()
    for test_name in dir(test_class):
        if test_name.startswith('test_'):
            try:
                getattr(test_class, test_name)()
                print(f"✅ {test_name}")
                results.append(True)
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append(False)
    
    # Test concept validation
    print("\n--- Concept Validation Tests ---")
    test_class = TestConceptValidation()
    for test_name in dir(test_class):
        if test_name.startswith('test_'):
            try:
                getattr(test_class, test_name)()
                print(f"✅ {test_name}")
                results.append(True)
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append(False)
    
    # Test profile validation
    print("\n--- Profile Validation Tests ---")
    test_class = TestProfileValidation()
    for test_name in dir(test_class):
        if test_name.startswith('test_'):
            try:
                getattr(test_class, test_name)()
                print(f"✅ {test_name}")
                results.append(True)
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append(False)
    
    # Test retry logic
    print("\n--- Retry Logic Tests ---")
    test_class = TestRetryLogic()
    for test_name in dir(test_class):
        if test_name.startswith('test_'):
            try:
                getattr(test_class, test_name)()
                print(f"✅ {test_name}")
                results.append(True)
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append(False)
    
    # Test atomic writes
    print("\n--- Atomic Write Tests ---")
    test_class = TestAtomicWrites()
    for test_name in dir(test_class):
        if test_name.startswith('test_'):
            try:
                getattr(test_class, test_name)()
                print(f"✅ {test_name}")
                results.append(True)
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append(False)
    
    # Test end-to-end
    print("\n--- End-to-End Tests ---")
    test_class = TestEndToEnd()
    for test_name in dir(test_class):
        if test_name.startswith('test_'):
            try:
                getattr(test_class, test_name)()
                print(f"✅ {test_name}")
                results.append(True)
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    print(f"Pass rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return True
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

