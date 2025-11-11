terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Model Performance Alarm - Gold Tier
resource "aws_cloudwatch_metric_alarm" "performance_gold" {
  alarm_name          = "srl-rlvr-performance-gold-tier"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelPerformance"
  namespace           = "Custom/SRL-RLVR"
  period              = 300
  statistic           = "Average"
  threshold           = 0.80  # 80% performance threshold
  alarm_description   = "Alert when Gold tier model performance drops below 80%"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  dimensions = {
    Tier = "Gold"
  }

  tags = {
    Tier       = "Gold"
    Purpose    = "Performance Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# Model Performance Alarm - Silver Tier
resource "aws_cloudwatch_metric_alarm" "performance_silver" {
  alarm_name          = "srl-rlvr-performance-silver-tier"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelPerformance"
  namespace           = "Custom/SRL-RLVR"
  period              = 300
  statistic           = "Average"
  threshold           = 0.85  # 85% performance threshold
  alarm_description   = "Alert when Silver tier model performance drops below 85%"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  dimensions = {
    Tier = "Silver"
  }

  tags = {
    Tier       = "Silver"
    Purpose    = "Performance Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# Model Performance Alarm - Bronze Tier
resource "aws_cloudwatch_metric_alarm" "performance_bronze" {
  alarm_name          = "srl-rlvr-performance-bronze-tier"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelPerformance"
  namespace           = "Custom/SRL-RLVR"
  period              = 300
  statistic           = "Average"
  threshold           = 0.90  # 90% performance threshold
  alarm_description   = "Alert when Bronze tier model performance drops below 90%"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  dimensions = {
    Tier = "Bronze"
  }

  tags = {
    Tier       = "Bronze"
    Purpose    = "Performance Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# Model Drift Alarm
resource "aws_cloudwatch_metric_alarm" "model_drift" {
  alarm_name          = "srl-rlvr-model-drift-detection"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ModelDrift"
  namespace           = "Custom/SRL-RLVR"
  period              = 3600
  statistic           = "Maximum"
  threshold           = 0.10  # 10% drift threshold
  alarm_description   = "Alert when model drift exceeds 10%"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  tags = {
    Purpose    = "Model Drift Detection"
    Component  = "SRL-RLVR Training"
  }
}

# Inference Latency Alarm - Gold Tier
resource "aws_cloudwatch_metric_alarm" "latency_gold" {
  alarm_name          = "srl-rlvr-latency-gold-tier"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "InferenceLatency"
  namespace           = "Custom/SRL-RLVR"
  period              = 60
  statistic           = "Average"
  threshold           = 200  # 200ms threshold
  alarm_description   = "Alert when Gold tier inference latency exceeds 200ms"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  dimensions = {
    Tier = "Gold"
  }

  tags = {
    Tier       = "Gold"
    Purpose    = "Latency Monitoring"
    Component  = "SRL-RLVR Training"
  }
}

# SNS Topic for Performance Alerts
resource "aws_sns_topic" "performance_alerts" {
  name = "srl-rlvr-performance-alerts"
  
  tags = {
    Purpose   = "Performance Alerting"
    Component = "SRL-RLVR Training"
  }
}

# SNS Topic Subscription (email)
resource "aws_sns_topic_subscription" "performance_alerts_email" {
  topic_arn = aws_sns_topic.performance_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

variable "alert_email" {
  description = "Email address for performance alerts"
  type        = string
  default     = ""
}





