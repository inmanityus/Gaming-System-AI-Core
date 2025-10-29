# Setup Media Download Environment for Be Free Fitness
# This script sets up the environment for downloading media from Shutterstock and Midjourney

Write-Host "🎯 Setting up media download environment for Be Free Fitness" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python is required but not installed." -ForegroundColor Red
    Write-Host "Please install Python 3 and try again." -ForegroundColor Yellow
    exit 1
}

# Install required Python packages
Write-Host "📦 Installing required Python packages..." -ForegroundColor Blue
pip install requests aiohttp

# Create environment file template
Write-Host "📝 Creating environment configuration template..." -ForegroundColor Blue

$envContent = @"
# Shutterstock API Configuration
# Get your credentials from: https://www.shutterstock.com/developers
SHUTTERSTOCK_CLIENT_ID=your_client_id_here
SHUTTERSTOCK_CLIENT_SECRET=your_client_secret_here

# Midjourney Discord Bot Configuration
# Create a Discord bot at: https://discord.com/developers/applications
DISCORD_BOT_TOKEN=your_bot_token_here
MIDJOURNEY_CHANNEL_ID=your_channel_id_here
"@

$envContent | Out-File -FilePath ".env.media" -Encoding UTF8

Write-Host "✅ Created .env.media template" -ForegroundColor Green

# Create directories
Write-Host "📁 Creating media directories..." -ForegroundColor Blue
$dirs = @(
    "apps/web/public/videos/hero",
    "apps/web/public/images/hero",
    "apps/web/public/images/services",
    "apps/web/public/images/testimonials",
    "apps/web/public/images/trainers",
    "apps/web/public/images/content"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "✅ Created directory structure" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Get Shutterstock API credentials:"
Write-Host "   - Visit https://www.shutterstock.com/developers"
Write-Host "   - Create an account and subscribe to a plan"
Write-Host "   - Create an application to get Client ID and Secret"
Write-Host ""
Write-Host "2. Get Midjourney Discord bot setup:"
Write-Host "   - Visit https://discord.com/developers/applications"
Write-Host "   - Create a new application and bot"
Write-Host "   - Invite bot to your Midjourney Discord server"
Write-Host "   - Get the channel ID where Midjourney bot is active"
Write-Host ""
Write-Host "3. Configure environment variables:"
Write-Host "   - Edit .env.media with your credentials"
Write-Host "   - Run the environment variable setup command"
Write-Host ""
Write-Host "4. Download media:"
Write-Host "   - For Shutterstock: python scripts/download-shutterstock-media.py"
Write-Host "   - For Midjourney: python scripts/download-midjourney-media.py"
Write-Host ""
Write-Host "📖 See docs/media-implementation-guide.md for detailed instructions" -ForegroundColor Cyan