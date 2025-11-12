#!/usr/bin/env python3
"""
Direct Vision Analysis Test
Tests GPT-4o vision analysis on Marvel Rivals screenshot
Bypasses orchestrator for immediate validation
"""

import os
import sys
import json
import base64
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_screenshot(screenshot_path: str, telemetry_path: str):
    """Analyze Marvel Rivals screenshot with GPT-4o"""
    
    print(f"\nAnalyzing: {os.path.basename(screenshot_path)}")
    print("=" * 60)
    
    # Load telemetry
    with open(telemetry_path, 'r') as f:
        telemetry = json.load(f)
    
    print(f"Event Type: {telemetry['event_type']}")
    print(f"Game: {telemetry['capture_trigger']['game_name']}")
    print(f"FPS: {telemetry['rendering_data']['current_fps']}")
    print()
    
    # Read and encode screenshot
    with open(screenshot_path, 'rb') as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare prompt
    prompt = f"""You are analyzing a screenshot from {telemetry['capture_trigger']['game_name']}, a competitive multiplayer game.

**Game Context:**
- Event: {telemetry['event_type']}
- FPS: {telemetry['rendering_data']['current_fps']}
- Resolution: {telemetry['rendering_data']['resolution']}

**Your Task: Evaluate Visual Quality and UX**

Analyze this screenshot for:

1. **UI/UX CLARITY**
   - Is UI readable and well-contrasted?
   - Are important elements clearly visible?
   - Is visual hierarchy effective?
   - Any UI obtrusiveness?

2. **VISUAL QUALITY**
   - Rendering quality
   - Lighting effectiveness
   - Color palette coherence
   - Any visual bugs (clipping, texture issues)?

3. **OVERALL ASSESSMENT**
   - What's working well?
   - What could be improved?
   - Any critical issues?

**Output Format (JSON):**
{{
  "confidence": 0.0-1.0,
  "is_issue": true/false,
  "category": "ux|visual_quality|performance",
  "issues_found": ["..."],
  "strengths": ["..."],
  "severity": "low|medium|high",
  "recommendations": ["..."]
}}"""

    print("Calling GPT-4o Vision API...")
    
    # Call GPT-4o vision
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    # Parse response
    result_text = response.choices[0].message.content
    
    print("\n" + "=" * 60)
    print("GPT-4o ANALYSIS RESULT:")
    print("=" * 60)
    
    try:
        result_json = json.loads(result_text)
        
        print(f"\nConfidence: {result_json.get('confidence', 0)*100:.1f}%")
        print(f"Issue Detected: {result_json.get('is_issue', False)}")
        print(f"Category: {result_json.get('category', 'unknown')}")
        print(f"Severity: {result_json.get('severity', 'unknown').upper()}")
        
        if result_json.get('strengths'):
            print(f"\nSTRENGTHS:")
            for strength in result_json['strengths']:
                print(f"   - {strength}")
        
        if result_json.get('issues_found'):
            print(f"\nISSUES FOUND:")
            for issue in result_json['issues_found']:
                print(f"   - {issue}")
        
        if result_json.get('recommendations'):
            print(f"\nRECOMMENDATIONS:")
            for rec in result_json['recommendations']:
                print(f"   - {rec}")
        
        # Save result
        output_file = screenshot_path.replace('.png', '_gpt4o_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(result_json, f, indent=2)
        
        print(f"\nAnalysis saved: {output_file}")
        
        return result_json
        
    except json.JSONDecodeError:
        print("\nWARNING: Model returned non-JSON response:")
        print(result_text)
        return None

def main():
    """Test with first Marvel Rivals capture"""
    base_dir = "unreal/GameObserver/Captures"
    
    # Find first capture
    screenshots = [f for f in os.listdir(base_dir) if f.endswith('.png')]
    
    if not screenshots:
        print("ERROR: No screenshots found in captures directory")
        return
    
    # Analyze first 3 captures
    print(f"\nFound {len(screenshots)} Marvel Rivals captures")
    print(f"Testing with first 3 screenshots...\n")
    
    for i, screenshot in enumerate(screenshots[:3], 1):
        screenshot_path = os.path.join(base_dir, screenshot)
        telemetry_path = screenshot_path.replace('.png', '.json')
        
        if not os.path.exists(telemetry_path):
            print(f"WARNING: Skipping {screenshot} - no telemetry file")
            continue
        
        print(f"\n{'='*60}")
        print(f"ANALYZING CAPTURE {i}/3")
        print(f"{'='*60}")
        
        result = analyze_screenshot(screenshot_path, telemetry_path)
        
        if i < 3:
            print("\nWaiting 2 seconds before next analysis...")
            import time
            time.sleep(2)
    
    print("\n" + "="*60)
    print("VISION ANALYSIS TEST COMPLETE")
    print("="*60)
    print("\nResults saved in captures directory (*_gpt4o_analysis.json)")
    print("Check files to see what GPT-4o detected in Marvel Rivals screenshots!")

if __name__ == "__main__":
    main()

