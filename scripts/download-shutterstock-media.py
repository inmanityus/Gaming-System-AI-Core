#!/usr/bin/env python3
"""
Shutterstock Media Downloader for Be Free Fitness
Downloads high-resolution images and videos from Shutterstock API
"""

import os
import requests
import json
import base64
from typing import List, Dict, Optional
import time

class ShutterstockDownloader:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.shutterstock.com/v2"
        
    def authenticate(self) -> bool:
        """Authenticate with Shutterstock API"""
        auth_url = f"{self.base_url}/oauth/access_token"
        
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            print("✓ Successfully authenticated with Shutterstock API")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def search_images(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search for images"""
        if not self.access_token:
            print("✗ Not authenticated. Call authenticate() first.")
            return []
        
        search_url = f"{self.base_url}/images/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {
            "query": query,
            "per_page": per_page,
            "image_type": "photo",
            "orientation": "horizontal",
            "people_model_released": "true"
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Search failed: {e}")
            return []
    
    def search_videos(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search for videos"""
        if not self.access_token:
            print("✗ Not authenticated. Call authenticate() first.")
            return []
        
        search_url = f"{self.base_url}/videos/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {
            "query": query,
            "per_page": per_page,
            "duration": "10-30",  # 10-30 second videos for hero sections
            "people_model_released": "true"
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Video search failed: {e}")
            return []
    
    def license_image(self, image_id: str, size: str = "huge") -> Optional[str]:
        """License an image and get download URL"""
        if not self.access_token:
            print("✗ Not authenticated. Call authenticate() first.")
            return None
        
        license_url = f"{self.base_url}/images/licenses"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "images": [{"image_id": image_id, "size": size}]
        }
        
        try:
            response = requests.post(license_url, headers=headers, json=data)
            response.raise_for_status()
            
            license_data = response.json()
            if license_data.get("data"):
                return license_data["data"][0].get("download", {}).get("url")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Licensing failed: {e}")
        
        return None
    
    def license_video(self, video_id: str, size: str = "hd") -> Optional[str]:
        """License a video and get download URL"""
        if not self.access_token:
            print("✗ Not authenticated. Call authenticate() first.")
            return None
        
        license_url = f"{self.base_url}/videos/licenses"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "videos": [{"video_id": video_id, "size": size}]
        }
        
        try:
            response = requests.post(license_url, headers=headers, json=data)
            response.raise_for_status()
            
            license_data = response.json()
            if license_data.get("data"):
                return license_data["data"][0].get("download", {}).get("url")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Video licensing failed: {e}")
        
        return None
    
    def download_file(self, url: str, filepath: str) -> bool:
        """Download a file from URL"""
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
    """Main function to download fitness media"""
    
    # Configuration
    CLIENT_ID = os.getenv("SHUTTERSTOCK_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SHUTTERSTOCK_CLIENT_SECRET")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("✗ Please set SHUTTERSTOCK_CLIENT_ID and SHUTTERSTOCK_CLIENT_SECRET environment variables")
        print("Get your API credentials from: https://www.shutterstock.com/developers")
        return
    
    # Initialize downloader
    downloader = ShutterstockDownloader(CLIENT_ID, CLIENT_SECRET)
    
    # Authenticate
    if not downloader.authenticate():
        return
    
    # Media requirements for Be Free Fitness
    media_requirements = [
        # Hero Videos
        {"type": "video", "query": "fitness workout squat", "filename": "homepage-hero.mp4", "folder": "videos/hero"},
        {"type": "video", "query": "personal trainer client", "filename": "about-hero.mp4", "folder": "videos/hero"},
        {"type": "video", "query": "gym workout montage", "filename": "services-hero.mp4", "folder": "videos/hero"},
        {"type": "video", "query": "person using phone fitness", "filename": "ai-analyzer-hero.mp4", "folder": "videos/hero"},
        {"type": "video", "query": "fitness gym facility", "filename": "contact-hero.mp4", "folder": "videos/hero"},
        {"type": "video", "query": "happy fitness client", "filename": "testimonials-hero.mp4", "folder": "videos/hero"},
        {"type": "video", "query": "personal trainer coaching", "filename": "trainers-hero.mp4", "folder": "videos/hero"},
        
        # Service Images
        {"type": "image", "query": "mobility exercises corrective", "filename": "corrective-training.jpg", "folder": "images/services"},
        {"type": "image", "query": "functional strength training", "filename": "functional-strength.jpg", "folder": "images/services"},
        {"type": "image", "query": "fitness app phone technology", "filename": "ai-movement-analysis.jpg", "folder": "images/services"},
        
        # Testimonial Photos
        {"type": "image", "query": "professional woman portrait", "filename": "sarah-m.jpg", "folder": "images/testimonials"},
        {"type": "image", "query": "male fitness trainer portrait", "filename": "mike-r.jpg", "folder": "images/testimonials"},
        {"type": "image", "query": "woman mother portrait", "filename": "jennifer-l.jpg", "folder": "images/testimonials"},
        
        # Trainer Photos
        {"type": "image", "query": "hispanic fitness trainer", "filename": "mike-rodriguez.jpg", "folder": "images/trainers"},
        {"type": "image", "query": "female fitness trainer", "filename": "sarah-johnson.jpg", "folder": "images/trainers"},
        {"type": "image", "query": "asian fitness trainer", "filename": "david-lee.jpg", "folder": "images/trainers"},
    ]
    
    print(f"\n🎯 Starting download of {len(media_requirements)} media assets...\n")
    
    for i, req in enumerate(media_requirements, 1):
        print(f"[{i}/{len(media_requirements)}] Searching for: {req['query']}")
        
        # Search for media
        if req["type"] == "video":
            results = downloader.search_videos(req["query"], per_page=5)
        else:
            results = downloader.search_images(req["query"], per_page=5)
        
        if not results:
            print(f"  ⚠ No results found for: {req['query']}")
            continue
        
        # Select first result
        media = results[0]
        media_id = media["id"]
        
        print(f"  📋 Found: {media.get('description', 'No description')[:50]}...")
        
        # License and download
        if req["type"] == "video":
            download_url = downloader.license_video(media_id, "hd")
        else:
            download_url = downloader.license_image(media_id, "huge")
        
        if download_url:
            filepath = f"apps/web/public/{req['folder']}/{req['filename']}"
            success = downloader.download_file(download_url, filepath)
            
            if success:
                print(f"  ✅ Successfully downloaded: {req['filename']}")
            else:
                print(f"  ❌ Failed to download: {req['filename']}")
        else:
            print(f"  ❌ Failed to license: {req['filename']}")
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n🎉 Download process completed!")
    print(f"📁 Check the apps/web/public/ directory for downloaded files")

if __name__ == "__main__":
    main()


