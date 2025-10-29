#!/bin/bash

# Setup Media Download Environment for Be Free Fitness
# This script sets up the environment for downloading media from Shutterstock and Midjourney

echo "🎯 Setting up media download environment for Be Free Fitness"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

echo "✅ Python 3 found"

# Install required Python packages
echo "📦 Installing required Python packages..."
pip3 install requests aiohttp

# Create environment file template
echo "📝 Creating environment configuration template..."

cat > .env.media << 'EOF'
# Shutterstock API Configuration
# Get your credentials from: https://www.shutterstock.com/developers
SHUTTERSTOCK_CLIENT_ID=your_client_id_here
SHUTTERSTOCK_CLIENT_SECRET=your_client_secret_here

# Midjourney Discord Bot Configuration
# Create a Discord bot at: https://discord.com/developers/applications
DISCORD_BOT_TOKEN=your_bot_token_here
MIDJOURNEY_CHANNEL_ID=your_channel_id_here
EOF

echo "✅ Created .env.media template"

# Create directories
echo "📁 Creating media directories..."
mkdir -p apps/web/public/videos/hero
mkdir -p apps/web/public/images/hero
mkdir -p apps/web/public/images/services
mkdir -p apps/web/public/images/testimonials
mkdir -p apps/web/public/images/trainers
mkdir -p apps/web/public/images/content

echo "✅ Created directory structure"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get Shutterstock API credentials:"
echo "   - Visit https://www.shutterstock.com/developers"
echo "   - Create an account and subscribe to a plan"
echo "   - Create an application to get Client ID and Secret"
echo ""
echo "2. Get Midjourney Discord bot setup:"
echo "   - Visit https://discord.com/developers/applications"
echo "   - Create a new application and bot"
echo "   - Invite bot to your Midjourney Discord server"
echo "   - Get the channel ID where Midjourney bot is active"
echo ""
echo "3. Configure environment variables:"
echo "   - Edit .env.media with your credentials"
echo "   - Run: source .env.media"
echo ""
echo "4. Download media:"
echo "   - For Shutterstock: python3 scripts/download-shutterstock-media.py"
echo "   - For Midjourney: python3 scripts/download-midjourney-media.py"
echo ""
echo "📖 See docs/media-implementation-guide.md for detailed instructions"


