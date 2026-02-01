#!/bin/bash
# MSIL MCP Server - AWS Deployment Script
# ========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   MSIL MCP Server - AWS Deployment${NC}"
echo -e "${GREEN}============================================${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}Error: Terraform is not installed${NC}"
        echo "Please install Terraform: https://www.terraform.io/downloads"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        echo "Please install AWS CLI: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${GREEN}All prerequisites met!${NC}"
}

# Check AWS credentials
check_aws_credentials() {
    echo -e "\n${YELLOW}Checking AWS credentials...${NC}"
    
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo -e "${GREEN}AWS credentials configured for account: ${ACCOUNT_ID}${NC}"
    else
        echo -e "${RED}Error: AWS credentials not configured${NC}"
        echo "Run 'aws configure' to set up your credentials"
        exit 1
    fi
}

# Check terraform.tfvars
check_tfvars() {
    echo -e "\n${YELLOW}Checking terraform.tfvars...${NC}"
    
    if [ ! -f "terraform.tfvars" ]; then
        echo -e "${RED}Error: terraform.tfvars not found${NC}"
        echo "Copy terraform.tfvars.example to terraform.tfvars and fill in your values"
        exit 1
    fi
    
    echo -e "${GREEN}terraform.tfvars found!${NC}"
}

# Create S3 backend bucket if not exists
create_backend() {
    echo -e "\n${YELLOW}Setting up Terraform backend...${NC}"
    
    BUCKET_NAME="msil-mcp-terraform-state"
    REGION="ap-south-1"
    
    if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        echo "Creating S3 bucket for Terraform state..."
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
        
        aws s3api put-bucket-versioning \
            --bucket "$BUCKET_NAME" \
            --versioning-configuration Status=Enabled
        
        aws s3api put-bucket-encryption \
            --bucket "$BUCKET_NAME" \
            --server-side-encryption-configuration '{
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            }'
        
        echo -e "${GREEN}S3 bucket created!${NC}"
    else
        echo -e "${GREEN}S3 bucket already exists${NC}"
    fi
    
    # Create DynamoDB table for state locking
    TABLE_NAME="msil-mcp-terraform-locks"
    
    if ! aws dynamodb describe-table --table-name "$TABLE_NAME" 2>/dev/null; then
        echo "Creating DynamoDB table for state locking..."
        aws dynamodb create-table \
            --table-name "$TABLE_NAME" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "$REGION"
        
        echo -e "${GREEN}DynamoDB table created!${NC}"
    else
        echo -e "${GREEN}DynamoDB table already exists${NC}"
    fi
}

# Initialize Terraform
init_terraform() {
    echo -e "\n${YELLOW}Initializing Terraform...${NC}"
    terraform init
    echo -e "${GREEN}Terraform initialized!${NC}"
}

# Validate Terraform configuration
validate_terraform() {
    echo -e "\n${YELLOW}Validating Terraform configuration...${NC}"
    terraform validate
    echo -e "${GREEN}Terraform configuration is valid!${NC}"
}

# Plan deployment
plan_deployment() {
    echo -e "\n${YELLOW}Creating deployment plan...${NC}"
    terraform plan -out=tfplan
    echo -e "${GREEN}Deployment plan created!${NC}"
}

# Apply deployment
apply_deployment() {
    echo -e "\n${YELLOW}Applying deployment...${NC}"
    read -p "Do you want to apply the deployment? (yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        terraform apply tfplan
        echo -e "${GREEN}Deployment completed!${NC}"
    else
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 0
    fi
}

# Build and push Docker images
build_and_push_images() {
    echo -e "\n${YELLOW}Building and pushing Docker images...${NC}"
    
    # Get ECR login
    aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com"
    
    # Build and push each image
    IMAGES=("mcp-server" "chat-ui" "admin-ui" "mock-api")
    
    for image in "${IMAGES[@]}"; do
        echo -e "\n${YELLOW}Building ${image}...${NC}"
        
        case $image in
            "mcp-server")
                docker build -t "${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev/${image}:latest" -f ../../mcp-server/Dockerfile ../../mcp-server
                ;;
            "chat-ui")
                docker build -t "${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev/${image}:latest" -f ../../chat-ui/Dockerfile ../../chat-ui
                ;;
            "admin-ui")
                docker build -t "${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev/${image}:latest" -f ../../admin-ui/Dockerfile ../../admin-ui
                ;;
            "mock-api")
                docker build -t "${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev/${image}:latest" -f ../../mock-api/Dockerfile ../../mock-api
                ;;
        esac
        
        echo -e "${YELLOW}Pushing ${image}...${NC}"
        docker push "${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev/${image}:latest"
    done
    
    echo -e "${GREEN}All images pushed!${NC}"
}

# Show outputs
show_outputs() {
    echo -e "\n${YELLOW}Deployment outputs:${NC}"
    terraform output
}

# Main execution
main() {
    case "${1:-deploy}" in
        "init")
            check_prerequisites
            check_aws_credentials
            create_backend
            init_terraform
            ;;
        "plan")
            check_tfvars
            plan_deployment
            ;;
        "apply")
            apply_deployment
            ;;
        "deploy")
            check_prerequisites
            check_aws_credentials
            check_tfvars
            create_backend
            init_terraform
            validate_terraform
            plan_deployment
            apply_deployment
            show_outputs
            ;;
        "images")
            check_prerequisites
            check_aws_credentials
            build_and_push_images
            ;;
        "destroy")
            echo -e "${RED}WARNING: This will destroy all infrastructure!${NC}"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" == "yes" ]; then
                terraform destroy
            fi
            ;;
        "outputs")
            show_outputs
            ;;
        *)
            echo "Usage: $0 {init|plan|apply|deploy|images|destroy|outputs}"
            echo ""
            echo "Commands:"
            echo "  init    - Initialize backend and Terraform"
            echo "  plan    - Create deployment plan"
            echo "  apply   - Apply deployment plan"
            echo "  deploy  - Full deployment (init + plan + apply)"
            echo "  images  - Build and push Docker images"
            echo "  destroy - Destroy all infrastructure"
            echo "  outputs - Show deployment outputs"
            exit 1
            ;;
    esac
}

main "$@"
