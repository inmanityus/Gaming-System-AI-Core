-- Be Free Fitness Database Schema
-- This script creates all necessary tables for the Be Free Fitness website

-- Create database if it doesn't exist (run this manually first)
-- CREATE DATABASE "befreefitness";

-- Connect to the database and create tables

-- User Groups table
CREATE TABLE IF NOT EXISTS user_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('Admin', 'Sales', 'Marketing', 'Trainer', 'Client')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    user_group_id INTEGER REFERENCES user_groups(id),
    auth_provider VARCHAR(20) CHECK (auth_provider IN ('email', 'google', 'apple')),
    google_id VARCHAR(255),
    apple_id VARCHAR(255),
    profile_picture VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_failed_login_at TIMESTAMP,
    last_failed_login_ip INET,
    first_login_at TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    required_fields JSONB DEFAULT '[]',
    optional_fields JSONB DEFAULT '[]',
    stylesheet_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Workflows table
CREATE TABLE IF NOT EXISTS email_workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    trigger_event VARCHAR(100) NOT NULL,
    template_id INTEGER REFERENCES email_templates(id),
    recipient_group_id INTEGER REFERENCES user_groups(id),
    conditions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Form Submissions table
CREATE TABLE IF NOT EXISTS form_submissions (
    id SERIAL PRIMARY KEY,
    form_type VARCHAR(50) NOT NULL CHECK (form_type IN ('contact', 'ai_diagnostic', 'intake', 'login')),
    user_id INTEGER REFERENCES users(id),
    submission_data JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    encrypted_file_path VARCHAR(500),
    file_size BIGINT NOT NULL,
    original_file_size BIGINT,
    encrypted_file_size BIGINT,
    mime_type VARCHAR(100) NOT NULL,
    encryption_iv VARCHAR(255),
    encryption_tag VARCHAR(255),
    is_encrypted BOOLEAN DEFAULT false,
    is_processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Access Tokens table
CREATE TABLE IF NOT EXISTS access_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wiki Questions table
CREATE TABLE IF NOT EXISTS wiki_questions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    is_answered BOOLEAN DEFAULT false,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wiki Answers table
CREATE TABLE IF NOT EXISTS wiki_answers (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES wiki_questions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    is_accepted BOOLEAN DEFAULT false,
    is_ai_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trainer Insights table
CREATE TABLE IF NOT EXISTS trainer_insights (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    question TEXT NOT NULL,
    fee_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'completed', 'cancelled')),
    assigned_trainer_id INTEGER REFERENCES users(id),
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Actions table (for tracking and reminders)
CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    data JSONB DEFAULT '{}',
    expires_at TIMESTAMP NOT NULL,
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client Progress table (for tracking intake form versions)
CREATE TABLE IF NOT EXISTS client_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    intake_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password Reset Tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security Events table (for audit logging)
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    ip_address INET,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions table (for session management)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Profiles table (extended user information)
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    height_cm INTEGER,
    weight_kg DECIMAL(5,2),
    fitness_level VARCHAR(20) CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
    primary_goals TEXT[], -- Array of fitness goals
    secondary_goals TEXT[],
    injuries TEXT[], -- Array of known injuries
    limitations TEXT[], -- Array of physical limitations
    preferred_workout_duration INTEGER, -- in minutes
    workout_frequency INTEGER, -- workouts per week
    available_equipment TEXT[], -- Array of available equipment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Physical Categories table
CREATE TABLE IF NOT EXISTS physical_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    icon VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exercises table
CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(100),
    summary TEXT NOT NULL,
    steps TEXT[] NOT NULL, -- Array of numbered steps
    target_areas JSONB NOT NULL, -- {"head": 0, "neck": 0, "shoulders": 75, "arms": 25, "core": 50, "hips": 0, "legs": 0, "ankles": 0, "feet": 0}
    estimated_duration INTEGER NOT NULL, -- in minutes
    optional_video_url VARCHAR(500),
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    equipment_required TEXT[], -- Array of required equipment
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workouts table (AI-assigned collections of exercises)
CREATE TABLE IF NOT EXISTS workouts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    total_duration INTEGER NOT NULL, -- in minutes
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    target_categories TEXT[], -- Array of target physical categories
    ai_assigned BOOLEAN DEFAULT true,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workout Exercises table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS workout_exercises (
    id SERIAL PRIMARY KEY,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    sets INTEGER DEFAULT 1,
    reps INTEGER,
    duration_seconds INTEGER, -- for time-based exercises
    rest_seconds INTEGER DEFAULT 30,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workout Sessions table (scheduled workouts)
CREATE TABLE IF NOT EXISTS workout_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    duration_minutes INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'skipped')),
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    actual_duration_minutes INTEGER,
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Progress Tracking table
CREATE TABLE IF NOT EXISTS progress_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workout_session_id INTEGER REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
    sets_completed INTEGER DEFAULT 0,
    reps_completed INTEGER DEFAULT 0,
    duration_completed INTEGER DEFAULT 0, -- in seconds
    weight_used DECIMAL(5,2), -- for weighted exercises
    difficulty_rating INTEGER CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),
    form_rating INTEGER CHECK (form_rating >= 1 AND form_rating <= 5),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Analysis Results table (enhanced)
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES videos(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL, -- 'movement_analysis', 'form_check', 'progress_tracking'
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    category_scores JSONB, -- {"shoulders": 85, "core": 70, "legs": 90}
    movement_patterns TEXT[],
    recommendations TEXT[],
    exercise_suggestions TEXT[],
    risk_factors TEXT[],
    improvement_areas TEXT[],
    raw_analysis_data JSONB,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_apple_id ON users(apple_id);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);
CREATE INDEX IF NOT EXISTS idx_form_submissions_type ON form_submissions(form_type);
CREATE INDEX IF NOT EXISTS idx_form_submissions_user ON form_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_user ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_encrypted ON videos(is_encrypted);
CREATE INDEX IF NOT EXISTS idx_access_tokens_token ON access_tokens(token);
CREATE INDEX IF NOT EXISTS idx_access_tokens_expires ON access_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_email ON security_events(email);
CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_exercises_active ON exercises(is_active);
CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_workouts_user ON workouts(user_id);
CREATE INDEX IF NOT EXISTS idx_workouts_active ON workouts(is_active);
CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout ON workout_exercises(workout_id);
CREATE INDEX IF NOT EXISTS idx_workout_exercises_exercise ON workout_exercises(exercise_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_user ON workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_date ON workout_sessions(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_status ON workout_sessions(status);
CREATE INDEX IF NOT EXISTS idx_progress_tracking_user ON progress_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_tracking_session ON progress_tracking(workout_session_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_user ON ai_analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_video ON ai_analysis_results(video_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_type ON ai_analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_wiki_questions_expires ON wiki_questions(expires_at);
CREATE INDEX IF NOT EXISTS idx_actions_expires ON actions(expires_at);

-- Insert default user groups
INSERT INTO user_groups (name, type, description) VALUES
('Admin', 'Admin', 'System administrators with full access'),
('Sales', 'Sales', 'Sales team members'),
('Marketing', 'Marketing', 'Marketing team members'),
('Trainer', 'Trainer', 'Certified trainers'),
('Client', 'Client', 'Regular clients')
ON CONFLICT (name) DO NOTHING;

-- Insert default email templates
INSERT INTO email_templates (name, subject, html_content, text_content, required_fields) VALUES
('video_submission_thank_you', 'Welcome to Your Fitness Journey!', 
'<h1>Hello {{first_name}}!</h1><p>Thank you for submitting your video. You are one step away from revitalizing your life!</p><p><a href="{{intake_form_url}}?token={{access_token}}">Complete Your Intake Form</a></p>',
'Hello {{first_name}}! Thank you for submitting your video. Complete your intake form at: {{intake_form_url}}?token={{access_token}}',
'["first_name", "intake_form_url", "access_token"]'),
('video_submission_alert', 'New Video Submission Alert',
'<h2>New Video Submission</h2><p>Client: {{first_name}} {{last_name}}</p><p>Email: {{email}}</p><p>Phone: {{phone}}</p>',
'New Video Submission - Client: {{first_name}} {{last_name}}, Email: {{email}}, Phone: {{phone}}',
'["first_name", "last_name", "email", "phone"]'),
('intake_form_thank_you', 'Thank You for Completing Your Intake Form',
'<h1>Thank You {{first_name}}!</h1><p>Your intake form has been received and is being processed.</p>',
'Thank you {{first_name}}! Your intake form has been received.',
'["first_name"]'),
('intake_form_alert', 'New Intake Form Submission',
'<h2>New Intake Form Submission</h2><p>Client: {{first_name}} {{last_name}}</p>',
'New Intake Form Submission - Client: {{first_name}} {{last_name}}',
'["first_name", "last_name"]')
ON CONFLICT (name) DO NOTHING;

-- Insert default email workflows
INSERT INTO email_workflows (name, trigger_event, template_id, recipient_group_id) VALUES
('video_submission_client_email', 'video_submitted', 
(SELECT id FROM email_templates WHERE name = 'video_submission_thank_you'),
(SELECT id FROM user_groups WHERE name = 'Client')),
('video_submission_sales_alert', 'video_submitted',
(SELECT id FROM email_templates WHERE name = 'video_submission_alert'),
(SELECT id FROM user_groups WHERE name = 'Sales')),
('intake_form_client_email', 'intake_form_submitted',
(SELECT id FROM email_templates WHERE name = 'intake_form_thank_you'),
(SELECT id FROM user_groups WHERE name = 'Client')),
('intake_form_sales_alert', 'intake_form_submitted',
(SELECT id FROM email_templates WHERE name = 'intake_form_alert'),
(SELECT id FROM user_groups WHERE name = 'Sales'))
ON CONFLICT (name) DO NOTHING;

-- Insert physical categories
INSERT INTO physical_categories (name, icon, description) VALUES
('Head', '🧠', 'Head and facial muscles'),
('Neck', '🦒', 'Neck and cervical spine'),
('Shoulders', '💪', 'Shoulder girdle and deltoids'),
('Arms', '🦾', 'Biceps, triceps, and forearms'),
('Core', '🏋️', 'Abdominals, obliques, and lower back'),
('Hips', '🦵', 'Hip flexors, glutes, and hip joints'),
('Legs', '🦵', 'Quadriceps, hamstrings, and calves'),
('Ankles', '🦶', 'Ankle joints and surrounding muscles'),
('Feet', '👣', 'Foot muscles and arches')
ON CONFLICT (name) DO NOTHING;

-- Insert sample exercises
INSERT INTO exercises (name, icon, summary, steps, target_areas, estimated_duration, difficulty_level, equipment_required) VALUES
('Push-ups', '💪', 'Classic upper body strength exercise targeting chest, shoulders, and triceps', 
 ARRAY['Start in plank position with hands shoulder-width apart', 'Lower chest to ground while keeping body straight', 'Push back up to starting position', 'Repeat for desired reps'],
 '{"head": 0, "neck": 0, "shoulders": 40, "arms": 30, "core": 30, "hips": 0, "legs": 0, "ankles": 0, "feet": 0}',
 5, 'beginner', '{}'),
 
('Squats', '🦵', 'Fundamental lower body exercise for legs and glutes',
 ARRAY['Stand with feet shoulder-width apart', 'Lower body by bending knees and hips', 'Keep chest up and knees over toes', 'Return to standing position'],
 '{"head": 0, "neck": 0, "shoulders": 0, "arms": 0, "core": 20, "hips": 40, "legs": 40, "ankles": 0, "feet": 0}',
 5, 'beginner', '{}'),
 
('Plank', '🏋️', 'Isometric core strengthening exercise',
 ARRAY['Start in push-up position', 'Lower to forearms', 'Keep body straight from head to heels', 'Hold position for desired time'],
 '{"head": 0, "neck": 10, "shoulders": 20, "arms": 20, "core": 50, "hips": 0, "legs": 0, "ankles": 0, "feet": 0}',
 3, 'beginner', '{}'),
 
('Deadlift', '🏋️‍♂️', 'Compound movement targeting posterior chain',
 ARRAY['Stand with feet hip-width apart, bar over mid-foot', 'Bend at hips and knees to grip bar', 'Keep chest up and back straight', 'Stand up by extending hips and knees', 'Lower bar with control'],
 '{"head": 0, "neck": 10, "shoulders": 20, "arms": 10, "core": 30, "hips": 30, "legs": 30, "ankles": 0, "feet": 0}',
 8, 'intermediate', '{"barbell", "weights"}'),
 
('Overhead Press', '💪', 'Shoulder and upper body strength exercise',
 ARRAY['Stand with feet shoulder-width apart', 'Hold weights at shoulder level', 'Press weights straight up overhead', 'Lower with control to starting position'],
 '{"head": 0, "neck": 10, "shoulders": 60, "arms": 30, "core": 20, "hips": 0, "legs": 0, "ankles": 0, "feet": 0}',
 6, 'intermediate', '{"dumbbells", "barbell"}'),
 
('Lunges', '🦵', 'Single-leg exercise for legs and glutes',
 ARRAY['Stand with feet hip-width apart', 'Step forward with one leg', 'Lower back knee toward ground', 'Push back to starting position', 'Repeat with other leg'],
 '{"head": 0, "neck": 0, "shoulders": 0, "arms": 0, "core": 10, "hips": 30, "legs": 60, "ankles": 0, "feet": 0}',
 7, 'beginner', '{}'),
 
('Pull-ups', '🦾', 'Upper body pulling exercise',
 ARRAY['Hang from bar with palms facing away', 'Pull body up until chin clears bar', 'Lower with control to full extension', 'Repeat for desired reps'],
 '{"head": 0, "neck": 0, "shoulders": 30, "arms": 40, "core": 30, "hips": 0, "legs": 0, "ankles": 0, "feet": 0}',
 8, 'advanced', '{"pull-up bar"}'),
 
('Burpees', '🔥', 'Full-body conditioning exercise',
 ARRAY['Start standing', 'Drop to push-up position', 'Perform push-up', 'Jump feet to hands', 'Jump up with arms overhead', 'Repeat sequence'],
 '{"head": 0, "neck": 0, "shoulders": 20, "arms": 20, "core": 30, "hips": 20, "legs": 20, "ankles": 0, "feet": 0}',
 10, 'intermediate', '{}')
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_user_groups_updated_at BEFORE UPDATE ON user_groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_workflows_updated_at BEFORE UPDATE ON email_workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_wiki_questions_updated_at BEFORE UPDATE ON wiki_questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_wiki_answers_updated_at BEFORE UPDATE ON wiki_answers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trainer_insights_updated_at BEFORE UPDATE ON trainer_insights FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_client_progress_updated_at BEFORE UPDATE ON client_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_exercises_updated_at BEFORE UPDATE ON exercises FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workouts_updated_at BEFORE UPDATE ON workouts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workout_sessions_updated_at BEFORE UPDATE ON workout_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
