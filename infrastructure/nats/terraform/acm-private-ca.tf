# ACM Private CA for NATS mTLS Certificates
# Creates private CA and generates certificates for NATS cluster

resource "aws_acmpca_certificate_authority" "nats_ca" {
  type = "ROOT"

  certificate_authority_configuration {
    key_algorithm     = "RSA_4096"
    signing_algorithm = "SHA512WITHRSA"

    subject {
      common_name  = "Gaming System NATS CA"
      organization = "Gaming System"
      organizational_unit = "Infrastructure"
      country      = "US"
    }
  }

  permanent_deletion_time_in_days = 7
  enabled                         = true

  tags = {
    Name        = "nats-ca-${var.environment}"
    Environment = var.environment
    Purpose     = "NATS mTLS certificates"
  }
}

# Certificate for the CA itself
resource "aws_acmpca_certificate" "nats_ca_cert" {
  certificate_authority_arn   = aws_acmpca_certificate_authority.nats_ca.arn
  certificate_signing_request = aws_acmpca_certificate_authority.nats_ca.certificate_signing_request
  signing_algorithm           = "SHA512WITHRSA"

  template_arn = "arn:aws:acmpca:::template/RootCACertificate/V1"

  validity {
    type  = "YEARS"
    value = 10
  }
}

# Install CA certificate
resource "aws_acmpca_certificate_authority_certificate" "nats_ca" {
  certificate_authority_arn = aws_acmpca_certificate_authority.nats_ca.arn

  certificate       = aws_acmpca_certificate.nats_ca_cert.certificate
  certificate_chain = aws_acmpca_certificate.nats_ca_cert.certificate_chain
}

# IAM role for certificate issuance
resource "aws_iam_role" "nats_cert_issuer" {
  name = "nats-cert-issuer-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "nats-cert-issuer-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "nats_cert_issuer_policy" {
  name = "nats-cert-issuer-policy"
  role = aws_iam_role.nats_cert_issuer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "acm-pca:IssueCertificate",
          "acm-pca:GetCertificate",
          "acm-pca:GetCertificateAuthorityCertificate"
        ]
        Resource = aws_acmpca_certificate_authority.nats_ca.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:nats/certs/*"
      }
    ]
  })
}

# Store CA certificate in Secrets Manager
resource "aws_secretsmanager_secret" "nats_ca_cert" {
  name        = "nats/certs/ca-cert"
  description = "NATS CA certificate for mTLS"

  tags = {
    Name        = "nats-ca-cert"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "nats_ca_cert" {
  secret_id     = aws_secretsmanager_secret.nats_ca_cert.id
  secret_string = aws_acmpca_certificate.nats_ca_cert.certificate
}

# Outputs
output "nats_ca_arn" {
  description = "ARN of NATS Private CA"
  value       = aws_acmpca_certificate_authority.nats_ca.arn
}

output "nats_ca_cert_secret_arn" {
  description = "ARN of secret containing CA certificate"
  value       = aws_secretsmanager_secret.nats_ca_cert.arn
}

