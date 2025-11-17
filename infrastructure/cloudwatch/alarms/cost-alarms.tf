terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Training Cost Alarm - Gold Tier
resource "aws_cloudwatch_metric_alarm" "training_cost_gold" {
  alarm_name          = "srl-rlvr-training-cost-gold-tier"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "TrainingJobCost"
  namespace           = "AWS/SageMaker"
  period              = 3600
  statistic           = "Sum"
  threshold           = 100  # $100 per hour
  alarm_description   = "Alert when Gold tier training costs exceed $100/hour"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    TrainingJobName = "srl-rlvr-gold-*"
  }

  tags = {
    Tier       = "Gold"
    Purpose    = "Cost Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# Training Cost Alarm - Silver Tier
resource "aws_cloudwatch_metric_alarm" "training_cost_silver" {
  alarm_name          = "srl-rlvr-training-cost-silver-tier"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "TrainingJobCost"
  namespace           = "AWS/SageMaker"
  period              = 3600
  statistic           = "Sum"
  threshold           = 500  # $500 per hour
  alarm_description   = "Alert when Silver tier training costs exceed $500/hour"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    TrainingJobName = "srl-rlvr-silver-*"
  }

  tags = {
    Tier       = "Silver"
    Purpose    = "Cost Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# Training Cost Alarm - Bronze Tier
resource "aws_cloudwatch_metric_alarm" "training_cost_bronze" {
  alarm_name          = "srl-rlvr-training-cost-bronze-tier"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "TrainingJobCost"
  namespace           = "AWS/SageMaker"
  period              = 3600
  statistic           = "Sum"
  threshold           = 2000  # $2000 per hour
  alarm_description   = "Alert when Bronze tier training costs exceed $2000/hour"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    TrainingJobName = "srl-rlvr-bronze-*"
  }

  tags = {
    Tier       = "Bronze"
    Purpose    = "Cost Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# Daily Budget Alarm
resource "aws_cloudwatch_metric_alarm" "daily_budget" {
  alarm_name          = "srl-rlvr-daily-budget-alert"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400
  statistic           = "Maximum"
  threshold           = 1000  # $1000 per day
  alarm_description   = "Alert when daily AWS charges exceed $1000"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = {
    Purpose    = "Budget Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# SNS Topic for Cost Alerts
resource "aws_sns_topic" "cost_alerts" {
  name = "srl-rlvr-cost-alerts"
  
  tags = {
    Purpose   = "Cost Alerting"
    Component = "SRL-RLVR Training"
  }
}

# SNS Topic Subscription (email)
resource "aws_sns_topic_subscription" "cost_alerts_email" {
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email  # Set via variable
}

variable "alert_email" {
  description = "Email address for cost alerts"
  type        = string
  default     = ""
}










