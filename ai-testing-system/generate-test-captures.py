#!/usr/bin/env python3
"""
Generate Synthetic Test Captures
Creates realistic test screenshots and telemetry for system validation
"""

import json
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import random

def create_test_screenshot(filename: str, scenario: str):
    """Create a test screenshot with scenario label"""
    # Create 1920x1080 image
    width, height = 1920, 1080
    
    # Choose colors based on scenario
    if "flat_lighting" in scenario:
        # Flat, mid-tone gray (bad for horror)
        bg_color = (128, 128, 128)
    elif "good_contrast" in scenario:
        # Dark with highlights (good for horror)
        bg_color = (30, 30, 40)
    elif "poor_contrast" in scenario:
        # Light background with light text (bad UX)
        bg_color = (220, 220, 220)
    else:
        bg_color = (50, 50, 60)
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add scenario text
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    text = f"TEST SCENARIO: {scenario.upper()}"
    
    # Draw text
    if "poor_contrast" in scenario:
        # Light text on light background (BAD)
        text_color = (240, 240, 240)
    else:
        text_color = (255, 255, 255)
    
    draw.text((100, 100), text, fill=text_color, font=font)
    
    # Add some visual elements to make it game-like
    if "good_contrast" in scenario:
        # Add bright highlights (good horror lighting)
        draw.ellipse([800, 400, 1000, 600], fill=(255, 200, 150))
    
    if "flat_lighting" in scenario:
        # Add evenly lit objects (bad horror)
        draw.rectangle([500, 400, 700, 700], fill=(140, 140, 140))
        draw.rectangle([800, 400, 1000, 700], fill=(150, 150, 150))
    
    # Add UI elements for UX testing
    draw.rectangle([50, 900, 300, 1000], fill=(60, 60, 70))
    draw.text((60, 920), "UI ELEMENT", fill=text_color)
    
    # Save image
    img.save(filename)
    print(f"Created: {filename}")

def create_test_telemetry(filename: str, scenario: str, event_type: str):
    """Create realistic telemetry JSON"""
    telemetry = {
        "screenshot_filename": os.path.basename(filename.replace('.json', '.png')),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "capture_trigger": {
            "event_type": event_type,
            "source": "TestScenario",
            "scenario": scenario
        },
        "player_data": {
            "location": {
                "x": random.uniform(1000, 2000),
                "y": random.uniform(5000, 8000),
                "z": random.uniform(200, 400)
            },
            "rotation": {
                "pitch": random.uniform(-30, 30),
                "yaw": random.uniform(0, 360),
                "roll": 0.0
            },
            "velocity": {
                "x": random.uniform(-100, 100),
                "y": random.uniform(-100, 100),
                "z": random.uniform(-50, 50)
            },
            "health": random.uniform(50, 100),
            "is_in_combat": random.choice([True, False])
        },
        "world_data": {
            "zone_name": f"Test_{scenario}",
            "current_objective_id": "OBJ_TestValidation",
            "active_light_sources": random.randint(2, 8),
            "time_of_day": None
        },
        "rendering_data": {
            "resolution": "1920x1080",
            "current_fps": random.randint(55, 62),
            "camera_fov": 90
        },
        "veil_focus": "Both",
        "test_metadata": {
            "is_synthetic": True,
            "scenario": scenario,
            "expected_issues": get_expected_issues(scenario)
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(telemetry, f, indent=2)
    
    print(f"Created: {filename}")

def get_expected_issues(scenario: str) -> list:
    """Define what issues should be detected for each scenario"""
    if "flat_lighting" in scenario:
        return ["atmosphere: flat lighting, no dramatic shadows"]
    elif "poor_contrast" in scenario:
        return ["ux: poor text contrast, readability issues"]
    elif "good_contrast" in scenario:
        return []  # No issues expected
    else:
        return []

def generate_test_suite():
    """Generate complete test suite with various scenarios"""
    output_dir = "../unreal/GameObserver/Captures"
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios = [
        ("flat_lighting_goreforge", "OnEnterNewZone"),
        ("good_contrast_scene", "Baseline"),
        ("poor_contrast_ui", "OnUIPopup"),
        ("baseline_test_1", "Baseline"),
        ("combat_damage_test", "OnPlayerDamage"),
        ("zone_transition", "OnEnterNewZone"),
    ]
    
    counter = 1
    for scenario, event_type in scenarios:
        # Generate screenshot
        screenshot_file = os.path.join(output_dir, f"{event_type}_{counter:04d}_{scenario}.png")
        create_test_screenshot(screenshot_file, scenario)
        
        # Generate telemetry
        telemetry_file = os.path.join(output_dir, f"{event_type}_{counter:04d}_{scenario}.json")
        create_test_telemetry(telemetry_file, scenario, event_type)
        
        counter += 1
    
    print(f"\n✅ Generated {len(scenarios)} test captures")
    print(f"Location: {output_dir}")
    print("\nNext steps:")
    print("1. Start Local Test Runner Agent: python ai-testing-system/local-test-runner/agent.py")
    print("2. Agent will detect files and upload to S3")
    print("3. Orchestrator will trigger vision analysis")
    print("4. View results in Triage Dashboard: http://localhost:3000")

if __name__ == "__main__":
    generate_test_suite()

