# Setup Personal Training System
# This script sets up the database tables and creates test data for the personal training system

param(
    [switch]$SkipTables,
    [switch]$SkipTestData
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up Personal Training System..." -ForegroundColor Green

# Database connection parameters
$DB_HOST = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$DB_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }
$DB_NAME = if ($env:DB_NAME) { $env:DB_NAME } else { "befreefitness" }
$DB_USER = if ($env:DB_USER) { $env:DB_USER } else { "postgres" }
$DB_PASS = if ($env:DB_PASS) { $env:DB_PASS } else { "" }

# Set PGPASSWORD environment variable for psql
if ($DB_PASS) {
    $env:PGPASSWORD = $DB_PASS
}

$PSQL_CMD = "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"

Write-Host "Database connection: ${DB_HOST}:${DB_PORT}/${DB_NAME} as ${DB_USER}" -ForegroundColor Yellow

if (-not $SkipTables) {
    Write-Host "Creating database tables..." -ForegroundColor Green
    
    $schemaFile = "E:\Vibe Code\Be Free Fitness\Website\apps\api\src\database\personal-training-schema.sql"
    if (Test-Path $schemaFile) {
        & $PSQL_CMD -f $schemaFile
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Database tables created successfully" -ForegroundColor Green
        } else {
            Write-Host "Failed to create database tables" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Schema file not found: $schemaFile" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Skipping table creation" -ForegroundColor Yellow
}

if (-not $SkipTestData) {
    Write-Host "Creating test data..." -ForegroundColor Green
    
    # Create test data SQL
    $testDataSQL = @"
-- Create test trainers with different tiers
INSERT INTO users (first_name, last_name, email, phone, user_group_id, trainer_tier, is_active, created_at) VALUES
('Sarah', 'Johnson', 'sarah.johnson@befreefitness.com', '555-0101', (SELECT id FROM user_groups WHERE type = 'trainer'), 'standard', true, CURRENT_TIMESTAMP),
('Mike', 'Chen', 'mike.chen@befreefitness.com', '555-0102', (SELECT id FROM user_groups WHERE type = 'trainer'), 'pro', true, CURRENT_TIMESTAMP),
('Emma', 'Williams', 'emma.williams@befreefitness.com', '555-0103', (SELECT id FROM user_groups WHERE type = 'trainer'), 'standard', true, CURRENT_TIMESTAMP),
('David', 'Rodriguez', 'david.rodriguez@befreefitness.com', '555-0104', (SELECT id FROM user_groups WHERE type = 'trainer'), 'pro', true, CURRENT_TIMESTAMP),
('Lisa', 'Thompson', 'lisa.thompson@befreefitness.com', '555-0105', (SELECT id FROM user_groups WHERE type = 'trainer'), 'super', true, CURRENT_TIMESTAMP),
('James', 'Brown', 'james.brown@befreefitness.com', '555-0106', (SELECT id FROM user_groups WHERE type = 'trainer'), 'standard', true, CURRENT_TIMESTAMP),
('Maria', 'Garcia', 'maria.garcia@befreefitness.com', '555-0107', (SELECT id FROM user_groups WHERE type = 'trainer'), 'pro', true, CURRENT_TIMESTAMP),
('Alex', 'Davis', 'alex.davis@befreefitness.com', '555-0108', (SELECT id FROM user_groups WHERE type = 'trainer'), 'super', true, CURRENT_TIMESTAMP),
('Jennifer', 'Wilson', 'jennifer.wilson@befreefitness.com', '555-0109', (SELECT id FROM user_groups WHERE type = 'trainer'), 'standard', true, CURRENT_TIMESTAMP),
('Robert', 'Martinez', 'robert.martinez@befreefitness.com', '555-0110', (SELECT id FROM user_groups WHERE type = 'trainer'), 'pro', true, CURRENT_TIMESTAMP)
ON CONFLICT (email) DO NOTHING;

-- Create test clients
INSERT INTO users (first_name, last_name, email, phone, user_group_id, is_active, created_at) VALUES
('John', 'Doe', 'john.doe@befreefitness.com', '555-0201', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Jane', 'Smith', 'jane.smith@befreefitness.com', '555-0202', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Michael', 'Johnson', 'michael.johnson@befreefitness.com', '555-0203', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Sarah', 'Brown', 'sarah.brown@befreefitness.com', '555-0204', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('David', 'Wilson', 'david.wilson@befreefitness.com', '555-0205', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Emily', 'Davis', 'emily.davis@befreefitness.com', '555-0206', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Christopher', 'Miller', 'christopher.miller@befreefitness.com', '555-0207', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Jessica', 'Garcia', 'jessica.garcia@befreefitness.com', '555-0208', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Matthew', 'Martinez', 'matthew.martinez@befreefitness.com', '555-0209', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Ashley', 'Anderson', 'ashley.anderson@befreefitness.com', '555-0210', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Daniel', 'Taylor', 'daniel.taylor@befreefitness.com', '555-0211', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Amanda', 'Thomas', 'amanda.thomas@befreefitness.com', '555-0212', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Joshua', 'Jackson', 'joshua.jackson@befreefitness.com', '555-0213', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP),
('Stephanie', 'White', 'stephanie.white@befreefitness.com', '555-0214', (SELECT id FROM user_groups WHERE type = 'client'), true, CURRENT_TIMESTAMP)
ON CONFLICT (email) DO NOTHING;

-- Create user profiles for trainers with locations
INSERT INTO user_profiles (user_id, location, bio, specialties, certifications) VALUES
((SELECT id FROM users WHERE email = 'sarah.johnson@befreefitness.com'), 'Los Angeles, CA', 'Certified personal trainer with 5 years experience', 'Weight Loss, Strength Training', 'NASM-CPT'),
((SELECT id FROM users WHERE email = 'mike.chen@befreefitness.com'), 'New York, NY', 'Professional trainer specializing in athletic performance', 'Athletic Performance, Injury Prevention', 'ACSM-CPT'),
((SELECT id FROM users WHERE email = 'emma.williams@befreefitness.com'), 'Chicago, IL', 'Fitness coach focused on functional movement', 'Functional Training, Mobility', 'ACE-CPT'),
((SELECT id FROM users WHERE email = 'david.rodriguez@befreefitness.com'), 'Houston, TX', 'Strength and conditioning specialist', 'Powerlifting, Bodybuilding', 'NSCA-CSCS'),
((SELECT id FROM users WHERE email = 'lisa.thompson@befreefitness.com'), 'Phoenix, AZ', 'Elite trainer for professional athletes', 'Sports Performance, Rehabilitation', 'NASM-CES'),
((SELECT id FROM users WHERE email = 'james.brown@befreefitness.com'), 'Philadelphia, PA', 'Holistic fitness approach', 'Yoga, Pilates, Strength Training', 'RYT-200'),
((SELECT id FROM users WHERE email = 'maria.garcia@befreefitness.com'), 'San Antonio, TX', 'Nutrition and fitness expert', 'Nutrition Coaching, Weight Management', 'Precision Nutrition'),
((SELECT id FROM users WHERE email = 'alex.davis@befreefitness.com'), 'San Diego, CA', 'Olympic lifting specialist', 'Olympic Weightlifting, CrossFit', 'USAW Level 2'),
((SELECT id FROM users WHERE email = 'jennifer.wilson@befreefitness.com'), 'Dallas, TX', 'Group fitness and personal training', 'Group Fitness, HIIT, Cardio', 'AFAA-GFI'),
((SELECT id FROM users WHERE email = 'robert.martinez@befreefitness.com'), 'San Jose, CA', 'Senior fitness and wellness coach', 'Senior Fitness, Chronic Disease Management', 'ACSM-EP')
ON CONFLICT (user_id) DO UPDATE SET
location = EXCLUDED.location,
bio = EXCLUDED.bio,
specialties = EXCLUDED.specialties,
certifications = EXCLUDED.certifications;

-- Create user profiles for clients with addresses
INSERT INTO user_profiles (user_id, location, bio) VALUES
((SELECT id FROM users WHERE email = 'john.doe@befreefitness.com'), 'Los Angeles, CA', 'Looking to get in shape and lose weight'),
((SELECT id FROM users WHERE email = 'jane.smith@befreefitness.com'), 'New York, NY', 'Want to build strength and confidence'),
((SELECT id FROM users WHERE email = 'michael.johnson@befreefitness.com'), 'Chicago, IL', 'Training for a marathon'),
((SELECT id FROM users WHERE email = 'sarah.brown@befreefitness.com'), 'Houston, TX', 'Post-pregnancy fitness journey'),
((SELECT id FROM users WHERE email = 'david.wilson@befreefitness.com'), 'Phoenix, AZ', 'Senior looking to maintain mobility'),
((SELECT id FROM users WHERE email = 'emily.davis@befreefitness.com'), 'Philadelphia, PA', 'Yoga and mindfulness enthusiast'),
((SELECT id FROM users WHERE email = 'christopher.miller@befreefitness.com'), 'San Antonio, TX', 'Busy professional seeking efficient workouts'),
((SELECT id FROM users WHERE email = 'jessica.garcia@befreefitness.com'), 'San Diego, CA', 'Beach body preparation'),
((SELECT id FROM users WHERE email = 'matthew.martinez@befreefitness.com'), 'Dallas, TX', 'Athletic performance improvement'),
((SELECT id FROM users WHERE email = 'ashley.anderson@befreefitness.com'), 'San Jose, CA', 'Weight loss and lifestyle change'),
((SELECT id FROM users WHERE email = 'daniel.taylor@befreefitness.com'), 'Los Angeles, CA', 'Rehabilitation after injury'),
((SELECT id FROM users WHERE email = 'amanda.thomas@befreefitness.com'), 'New York, NY', 'Competitive bodybuilding prep'),
((SELECT id FROM users WHERE email = 'joshua.jackson@befreefitness.com'), 'Chicago, IL', 'Functional fitness for daily life'),
((SELECT id FROM users WHERE email = 'stephanie.white@befreefitness.com'), 'Houston, TX', 'Prenatal and postnatal fitness')
ON CONFLICT (user_id) DO UPDATE SET
location = EXCLUDED.location,
bio = EXCLUDED.bio;

-- Update users table with addresses for clients
UPDATE users SET address = '123 Main St, Los Angeles, CA 90210' WHERE email = 'john.doe@befreefitness.com';
UPDATE users SET address = '456 Broadway, New York, NY 10001' WHERE email = 'jane.smith@befreefitness.com';
UPDATE users SET address = '789 Michigan Ave, Chicago, IL 60601' WHERE email = 'michael.johnson@befreefitness.com';
UPDATE users SET address = '321 Main St, Houston, TX 77001' WHERE email = 'sarah.brown@befreefitness.com';
UPDATE users SET address = '654 Central Ave, Phoenix, AZ 85001' WHERE email = 'david.wilson@befreefitness.com';
UPDATE users SET address = '987 Market St, Philadelphia, PA 19101' WHERE email = 'emily.davis@befreefitness.com';
UPDATE users SET address = '147 Alamo Plaza, San Antonio, TX 78201' WHERE email = 'christopher.miller@befreefitness.com';
UPDATE users SET address = '258 Gaslamp Quarter, San Diego, CA 92101' WHERE email = 'jessica.garcia@befreefitness.com';
UPDATE users SET address = '369 Deep Ellum, Dallas, TX 75201' WHERE email = 'matthew.martinez@befreefitness.com';
UPDATE users SET address = '741 Silicon Valley Blvd, San Jose, CA 95101' WHERE email = 'ashley.anderson@befreefitness.com';
UPDATE users SET address = '852 Sunset Blvd, Los Angeles, CA 90028' WHERE email = 'daniel.taylor@befreefitness.com';
UPDATE users SET address = '963 5th Ave, New York, NY 10021' WHERE email = 'amanda.thomas@befreefitness.com';
UPDATE users SET address = '159 State St, Chicago, IL 60602' WHERE email = 'joshua.jackson@befreefitness.com';
UPDATE users SET address = '357 Main St, Houston, TX 77002' WHERE email = 'stephanie.white@befreefitness.com';

-- Create some existing client-trainer relationships
INSERT INTO client_trainer_relationships (client_id, trainer_id, status, started_at) VALUES
((SELECT id FROM users WHERE email = 'john.doe@befreefitness.com'), (SELECT id FROM users WHERE email = 'sarah.johnson@befreefitness.com'), 'active', CURRENT_TIMESTAMP),
((SELECT id FROM users WHERE email = 'jane.smith@befreefitness.com'), (SELECT id FROM users WHERE email = 'mike.chen@befreefitness.com'), 'active', CURRENT_TIMESTAMP),
((SELECT id FROM users WHERE email = 'michael.johnson@befreefitness.com'), (SELECT id FROM users WHERE email = 'lisa.thompson@befreefitness.com'), 'active', CURRENT_TIMESTAMP);

-- Create some trainer response templates
INSERT INTO trainer_response_templates (trainer_id, template_name, introduction, training_location, specialties, is_default) VALUES
((SELECT id FROM users WHERE email = 'sarah.johnson@befreefitness.com'), 'Standard Introduction', 'Hi! I''m Sarah, a certified personal trainer with 5 years of experience helping people achieve their fitness goals. I specialize in creating personalized workout plans that fit your lifestyle and help you see real results.', 'Los Angeles, CA - Home visits and gym sessions available', 'Weight Loss, Strength Training, Nutrition Guidance', true),
((SELECT id FROM users WHERE email = 'mike.chen@befreefitness.com'), 'Athletic Performance', 'Hello! I''m Mike, a professional trainer specializing in athletic performance and injury prevention. I work with athletes and active individuals to help them reach peak performance safely.', 'New York, NY - Multiple gym locations', 'Athletic Performance, Injury Prevention, Sports-Specific Training', true),
((SELECT id FROM users WHERE email = 'lisa.thompson@befreefitness.com'), 'Elite Training', 'Hi there! I''m Lisa, an elite trainer who works with professional athletes and high-performing individuals. My approach combines cutting-edge training methods with proven results.', 'Phoenix, AZ - Elite Training Facility', 'Sports Performance, Rehabilitation, Advanced Training Techniques', true);

-- Add profile images for all users (using Unsplash images)
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face' WHERE email = 'sarah.johnson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face' WHERE email = 'mike.chen@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face' WHERE email = 'emma.williams@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face' WHERE email = 'david.rodriguez@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face' WHERE email = 'lisa.thompson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face' WHERE email = 'james.brown@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=face' WHERE email = 'maria.garcia@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=150&h=150&fit=crop&crop=face' WHERE email = 'alex.davis@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=150&h=150&fit=crop&crop=face' WHERE email = 'jennifer.wilson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=face' WHERE email = 'robert.martinez@befreefitness.com';

-- Client profile images
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face' WHERE email = 'john.doe@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face' WHERE email = 'jane.smith@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face' WHERE email = 'michael.johnson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face' WHERE email = 'sarah.brown@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face' WHERE email = 'david.wilson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=face' WHERE email = 'emily.davis@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=150&h=150&fit=crop&crop=face' WHERE email = 'christopher.miller@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=150&h=150&fit=crop&crop=face' WHERE email = 'jessica.garcia@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=face' WHERE email = 'matthew.martinez@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face' WHERE email = 'ashley.anderson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face' WHERE email = 'daniel.taylor@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face' WHERE email = 'amanda.thomas@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face' WHERE email = 'joshua.jackson@befreefitness.com';
UPDATE users SET profile_image_url = 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face' WHERE email = 'stephanie.white@befreefitness.com';
"@

    # Write test data to temporary file
    $testDataFile = [System.IO.Path]::GetTempFileName() + ".sql"
    $testDataSQL | Out-File -FilePath $testDataFile -Encoding UTF8
    
    try {
        & $PSQL_CMD -f $testDataFile
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Test data created successfully" -ForegroundColor Green
        } else {
            Write-Host "Failed to create test data" -ForegroundColor Red
            exit 1
        }
    } finally {
        Remove-Item $testDataFile -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "Skipping test data creation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Personal Training System Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- Database tables created" -ForegroundColor White
Write-Host "- 10 Trainers created (Standard, Pro, Super tiers)" -ForegroundColor White
Write-Host "- 14 Clients created" -ForegroundColor White
Write-Host "- 3 Active client-trainer relationships" -ForegroundColor White
Write-Host "- Response templates created" -ForegroundColor White
Write-Host "- Profile images assigned" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "- Start the web server to test the personal training sidebar" -ForegroundColor White
Write-Host "- Create the remaining API endpoints for client responses" -ForegroundColor White
Write-Host "- Implement the billing daemon" -ForegroundColor White
Write-Host "- Build the cancellation workflow" -ForegroundColor White
