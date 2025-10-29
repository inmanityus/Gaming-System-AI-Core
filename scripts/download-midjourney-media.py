#!/usr/bin/env python3
"""
Midjourney Media Generator for Be Free Fitness
Generates high-quality AI images using Midjourney via Discord bot automation
"""

import os
import json
import time
import requests
from typing import List, Dict, Optional
import asyncio
import aiohttp

class MidjourneyGenerator:
    def __init__(self, discord_token: str, channel_id: str):
        self.discord_token = discord_token
        self.channel_id = channel_id
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {discord_token}",
            "Content-Type": "application/json"
        }
    
    def send_imagine_command(self, prompt: str) -> Optional[str]:
        """Send /imagine command to Discord channel"""
        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        
        # Enhanced prompts for fitness content
        enhanced_prompt = f"{prompt} --quality 2 --v 6 --ar 16:9 --style raw"
        
        payload = {
            "content": f"/imagine prompt: {enhanced_prompt}"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            message_data = response.json()
            print(f"✓ Sent imagine command: {prompt[:50]}...")
            return message_data.get("id")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to send imagine command: {e}")
            return None
    
    def get_channel_messages(self, limit: int = 10) -> List[Dict]:
        """Get recent messages from Discord channel"""
        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        params = {"limit": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get messages: {e}")
            return []
    
    def find_generated_images(self, message_id: str) -> List[str]:
        """Find generated images in Discord messages"""
        messages = self.get_channel_messages(20)
        image_urls = []
        
        for message in messages:
            if message.get("id") == message_id:
                # Look for attachments
                for attachment in message.get("attachments", []):
                    if attachment.get("content_type", "").startswith("image/"):
                        image_urls.append(attachment["url"])
                
                # Look for embeds
                for embed in message.get("embeds", []):
                    if embed.get("image"):
                        image_urls.append(embed["image"]["url"])
        
        return image_urls
    
    def download_image(self, url: str, filepath: str) -> bool:
        """Download image from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Downloaded: {filepath}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Download failed: {e}")
            return False

def main():
    """Main function to generate fitness images with Midjourney"""
    
    # Configuration
    DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    CHANNEL_ID = os.getenv("MIDJOURNEY_CHANNEL_ID")
    
    if not DISCORD_TOKEN or not CHANNEL_ID:
        print("✗ Please set DISCORD_BOT_TOKEN and MIDJOURNEY_CHANNEL_ID environment variables")
        print("Instructions:")
        print("1. Create a Discord bot at https://discord.com/developers/applications")
        print("2. Get the bot token and invite it to your Midjourney Discord server")
        print("3. Get the channel ID where Midjourney bot is active")
        return
    
    # Initialize generator
    generator = MidjourneyGenerator(DISCORD_TOKEN, CHANNEL_ID)
    
    # Fitness image prompts for Be Free Fitness
    image_prompts = [
        # Hero Images
        {
            "prompt": "Professional fitness trainer working with client in modern gym, high energy, motivational, cinematic lighting, 8K resolution",
            "filename": "homepage-hero.jpg",
            "folder": "images/hero"
        },
        {
            "prompt": "Person performing corrective mobility exercises, stretching, pain relief, therapeutic, professional, clean background",
            "filename": "corrective-training.jpg", 
            "folder": "images/services"
        },
        {
            "prompt": "Athlete performing functional strength training, kettlebell, deadlift, real-world movement, powerful, dynamic",
            "filename": "functional-strength.jpg",
            "folder": "images/services"
        },
        {
            "prompt": "Person using smartphone to record fitness movement, AI analysis, technology, modern, clean, professional",
            "filename": "ai-movement-analysis.jpg",
            "folder": "images/services"
        },
        {
            "prompt": "Professional headshot of confident woman in fitness attire, marketing professional, friendly, approachable, studio lighting",
            "filename": "sarah-m.jpg",
            "folder": "images/testimonials"
        },
        {
            "prompt": "Professional headshot of male fitness trainer, certified, experienced, trustworthy, studio portrait, clean background",
            "filename": "mike-r.jpg",
            "folder": "images/testimonials"
        },
        {
            "prompt": "Professional headshot of young mother, busy lifestyle, approachable, friendly, natural lighting, clean background",
            "filename": "jennifer-l.jpg",
            "folder": "images/testimonials"
        },
        {
            "prompt": "Hispanic male fitness trainer, professional headshot, experienced, confident, studio lighting, clean background",
            "filename": "mike-rodriguez.jpg",
            "folder": "images/trainers"
        },
        {
            "prompt": "Female fitness trainer, strength coach, professional headshot, confident, experienced, studio portrait",
            "filename": "sarah-johnson.jpg",
            "folder": "images/trainers"
        },
        {
            "prompt": "Asian male physical therapist, pain specialist, professional headshot, caring, experienced, medical professional",
            "filename": "david-lee.jpg",
            "folder": "images/trainers"
        }
    ]
    
    print(f"\n🎨 Starting generation of {len(image_prompts)} AI images with Midjourney...\n")
    
    for i, prompt_data in enumerate(image_prompts, 1):
        print(f"[{i}/{len(image_prompts)}] Generating: {prompt_data['filename']}")
        
        # Send imagine command
        message_id = generator.send_imagine_command(prompt_data["prompt"])
        
        if not message_id:
            print(f"  ❌ Failed to send command for: {prompt_data['filename']}")
            continue
        
        print(f"  ⏳ Waiting for image generation (this may take 1-2 minutes)...")
        
        # Wait for generation
        time.sleep(120)  # Wait 2 minutes for generation
        
        # Find and download generated images
        image_urls = generator.find_generated_images(message_id)
        
        if image_urls:
            # Download the first (best) image
            filepath = f"apps/web/public/{prompt_data['folder']}/{prompt_data['filename']}"
            success = generator.download_image(image_urls[0], filepath)
            
            if success:
                print(f"  ✅ Successfully generated: {prompt_data['filename']}")
            else:
                print(f"  ❌ Failed to download: {prompt_data['filename']}")
        else:
            print(f"  ⚠ No images found for: {prompt_data['filename']}")
        
        # Rate limiting between generations
        if i < len(image_prompts):
            print(f"  ⏳ Waiting 30 seconds before next generation...")
            time.sleep(30)
    
    print(f"\n🎉 Image generation process completed!")
    print(f"📁 Check the apps/web/public/ directory for generated files")

if __name__ == "__main__":
    main()


