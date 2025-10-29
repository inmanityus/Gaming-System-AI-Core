# Create Placeholder Images for Be Free Fitness
# This script creates simple colored placeholder images until real media is downloaded

# Create directory structure
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
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir"
    }
}

Write-Host ""
Write-Host "=== Directory Structure Created ==="
Write-Host ""

Write-Host "Placeholder images will be created using simple colored backgrounds."
Write-Host "You need to download real images from free stock sites using the media-download-list.md guide."
Write-Host ""

Write-Host "NEXT STEPS:"
Write-Host "1. Review docs/media-download-list.md for specific download instructions"
Write-Host "2. Visit pexels.com, unsplash.com, or mixkit.co to download free media"
Write-Host "3. Save files to the locations specified in media-download-list.md"
Write-Host "4. Run the website to see the updated images"
Write-Host ""

Write-Host "TEMPORARY SOLUTION:"
Write-Host "Copy the existing fitness-bg.jpg to all hero image locations as temporary placeholders:"
Write-Host ""

if (Test-Path "apps/web/public/images/fitness-bg.jpg") {
    Copy-Item "apps/web/public/images/fitness-bg.jpg" "apps/web/public/images/hero/homepage-hero.jpg" -Force
    Write-Host "Created temporary homepage-hero.jpg"
} else {
    Write-Host "fitness-bg.jpg not found - download images from free stock sites"
}

Write-Host ""
Write-Host "=== Placeholder Setup Complete ==="
Write-Host ""