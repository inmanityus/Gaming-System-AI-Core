#!/bin/bash

# Email System Setup Script for Be Free Fitness
# This script sets up and tests the email system

echo "🚀 Setting up Be Free Fitness Email System..."

# Function to test SMTP connection
test_smtp() {
    local host=$1
    local port=$2
    local name=$3
    
    echo "Testing $name connection ($host:$port)..."
    
    if timeout 10 bash -c "</dev/tcp/$host/$port"; then
        echo "✅ $name is accessible"
        return 0
    else
        echo "❌ $name is not accessible"
        return 1
    fi
}

# Function to send test email
send_test_email() {
    local smtp_host=$1
    local smtp_port=$2
    local smtp_user=$3
    local smtp_pass=$4
    local smtp_from=$5
    local test_email=$6
    
    echo "Sending test email via $smtp_host:$smtp_port..."
    
    # Create a simple test email
    cat << EOF | curl -s --url "smtp://$smtp_host:$smtp_port" \
        --mail-from "$smtp_from" \
        --mail-rcpt "$test_email" \
        --user "$smtp_user:$smtp_pass" \
        --upload-file -
From: $smtp_from
To: $test_email
Subject: Be Free Fitness Email System Test
Date: $(date -R)

Hello!

This is a test email from the Be Free Fitness email system.

If you receive this email, the SMTP server is working correctly.

Best regards,
Be Free Fitness Team
EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Test email sent successfully"
    else
        echo "❌ Failed to send test email"
    fi
}

# Test MailHog (Development)
echo ""
echo "📧 Testing MailHog (Development SMTP)..."
if test_smtp "localhost" "1025" "MailHog SMTP"; then
    echo "MailHog is running and accessible"
    echo "📱 You can view emails at: http://localhost:8025"
else
    echo "MailHog is not running. Start it with: docker-compose up mailhog"
fi

# Test Postfix (Alternative Development)
echo ""
echo "📧 Testing Postfix (Alternative Development SMTP)..."
if test_smtp "localhost" "25" "Postfix SMTP"; then
    echo "Postfix is running and accessible"
else
    echo "Postfix is not running. Start it with: docker-compose up postfix"
fi

# Test API Email Service
echo ""
echo "🔧 Testing API Email Service..."
if curl -s http://localhost:4000/api/email/test > /dev/null; then
    echo "✅ Email API endpoint is accessible"
else
    echo "❌ Email API endpoint is not accessible"
fi

# Create email testing script
echo ""
echo "📝 Creating email testing script..."

cat > test-email.sh << 'EOF'
#!/bin/bash

# Email Testing Script for Be Free Fitness
# Usage: ./test-email.sh [template_name] [recipient_email]

TEMPLATE_NAME=${1:-"video_submission_thank_you"}
RECIPIENT_EMAIL=${2:-"test@befreefitness.local"}

echo "🧪 Testing email template: $TEMPLATE_NAME"
echo "📧 Sending to: $RECIPIENT_EMAIL"

# Test data
TEST_DATA='{
    "first_name": "John",
    "last_name": "Doe",
    "email": "'$RECIPIENT_EMAIL'",
    "intake_form_url": "http://localhost:3000/intake",
    "access_token": "test-token-12345"
}'

# Send test email via API
curl -X POST http://localhost:4000/api/email/test \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
    -d '{
        "to": "'$RECIPIENT_EMAIL'",
        "templateName": "'$TEMPLATE_NAME'",
        "data": '$TEST_DATA'
    }'

echo ""
echo "✅ Test email sent!"
echo "📱 Check MailHog at: http://localhost:8025"
EOF

chmod +x test-email.sh

echo ""
echo "🎉 Email system setup complete!"
echo ""
echo "📋 Available SMTP servers:"
echo "   • MailHog (Development): localhost:1025"
echo "   • Postfix (Alternative): localhost:25"
echo ""
echo "🔧 Configuration files:"
echo "   • Email config: Docker-Template/email-config.env"
echo "   • Postfix config: Docker-Template/postfix/config/"
echo ""
echo "🧪 Testing:"
echo "   • Run: ./test-email.sh [template] [email]"
echo "   • View emails: http://localhost:8025 (MailHog)"
echo "   • API test: http://localhost:4000/api/email/test"
echo ""
echo "📚 Available email templates:"
echo "   • video_submission_thank_you"
echo "   • video_submission_alert"
echo "   • intake_form_thank_you"
echo "   • intake_form_alert"
echo "   • contact_form_alert"
echo "   • ai_analysis_complete"
