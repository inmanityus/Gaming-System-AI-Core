# Remote state configuration
# This should be configured after creating the S3 bucket for Terraform state

# terraform {
#   backend "s3" {
#     bucket         = "ai-core-terraform-state-695353648052"
#     key            = "network/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "ai-core-terraform-locks"
#   }
# }

# For now, we'll use local state
# To migrate to remote state:
# 1. Create S3 bucket: ai-core-terraform-state-695353648052
# 2. Create DynamoDB table: ai-core-terraform-locks
# 3. Uncomment the above backend configuration
# 4. Run: terraform init -migrate-state
