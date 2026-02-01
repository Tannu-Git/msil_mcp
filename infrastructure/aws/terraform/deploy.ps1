# MSIL MCP Server - AWS Deployment Script (PowerShell)
# =====================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("init", "plan", "apply", "deploy", "images", "destroy", "outputs")]
    [string]$Command = "deploy"
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "============================================" "Green"
Write-ColorOutput "   MSIL MCP Server - AWS Deployment" "Green"
Write-ColorOutput "============================================" "Green"

function Test-Prerequisites {
    Write-ColorOutput "`nChecking prerequisites..." "Yellow"
    
    if (!(Get-Command terraform -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Error: Terraform is not installed" "Red"
        Write-ColorOutput "Please install Terraform: https://www.terraform.io/downloads" "Red"
        exit 1
    }
    
    if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Error: AWS CLI is not installed" "Red"
        Write-ColorOutput "Please install AWS CLI: https://aws.amazon.com/cli/" "Red"
        exit 1
    }
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Error: Docker is not installed" "Red"
        Write-ColorOutput "Please install Docker: https://docs.docker.com/get-docker/" "Red"
        exit 1
    }
    
    Write-ColorOutput "All prerequisites met!" "Green"
}

function Test-AWSCredentials {
    Write-ColorOutput "`nChecking AWS credentials..." "Yellow"
    
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        $script:ACCOUNT_ID = $identity.Account
        Write-ColorOutput "AWS credentials configured for account: $($script:ACCOUNT_ID)" "Green"
    }
    catch {
        Write-ColorOutput "Error: AWS credentials not configured" "Red"
        Write-ColorOutput "Run 'aws configure' to set up your credentials" "Red"
        exit 1
    }
}

function Test-TfVars {
    Write-ColorOutput "`nChecking terraform.tfvars..." "Yellow"
    
    if (!(Test-Path "terraform.tfvars")) {
        Write-ColorOutput "Error: terraform.tfvars not found" "Red"
        Write-ColorOutput "Copy terraform.tfvars.example to terraform.tfvars and fill in your values" "Red"
        exit 1
    }
    
    Write-ColorOutput "terraform.tfvars found!" "Green"
}

function Initialize-Backend {
    Write-ColorOutput "`nSetting up Terraform backend..." "Yellow"
    
    $BUCKET_NAME = "msil-mcp-terraform-state"
    $REGION = "ap-south-1"
    
    # Check if bucket exists
    $bucketExists = aws s3api head-bucket --bucket $BUCKET_NAME 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Creating S3 bucket for Terraform state..." "Yellow"
        
        aws s3api create-bucket `
            --bucket $BUCKET_NAME `
            --region $REGION `
            --create-bucket-configuration LocationConstraint=$REGION
        
        aws s3api put-bucket-versioning `
            --bucket $BUCKET_NAME `
            --versioning-configuration Status=Enabled
        
        aws s3api put-bucket-encryption `
            --bucket $BUCKET_NAME `
            --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}'
        
        Write-ColorOutput "S3 bucket created!" "Green"
    }
    else {
        Write-ColorOutput "S3 bucket already exists" "Green"
    }
    
    # Check if DynamoDB table exists
    $TABLE_NAME = "msil-mcp-terraform-locks"
    $tableExists = aws dynamodb describe-table --table-name $TABLE_NAME 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Creating DynamoDB table for state locking..." "Yellow"
        
        aws dynamodb create-table `
            --table-name $TABLE_NAME `
            --attribute-definitions AttributeName=LockID,AttributeType=S `
            --key-schema AttributeName=LockID,KeyType=HASH `
            --billing-mode PAY_PER_REQUEST `
            --region $REGION
        
        Write-ColorOutput "DynamoDB table created!" "Green"
    }
    else {
        Write-ColorOutput "DynamoDB table already exists" "Green"
    }
}

function Initialize-Terraform {
    Write-ColorOutput "`nInitializing Terraform..." "Yellow"
    terraform init
    Write-ColorOutput "Terraform initialized!" "Green"
}

function Test-TerraformConfig {
    Write-ColorOutput "`nValidating Terraform configuration..." "Yellow"
    terraform validate
    Write-ColorOutput "Terraform configuration is valid!" "Green"
}

function New-DeploymentPlan {
    Write-ColorOutput "`nCreating deployment plan..." "Yellow"
    terraform plan -out=tfplan
    Write-ColorOutput "Deployment plan created!" "Green"
}

function Invoke-Deployment {
    Write-ColorOutput "`nApplying deployment..." "Yellow"
    $confirm = Read-Host "Do you want to apply the deployment? (yes/no)"
    
    if ($confirm -eq "yes") {
        terraform apply tfplan
        Write-ColorOutput "Deployment completed!" "Green"
    }
    else {
        Write-ColorOutput "Deployment cancelled" "Yellow"
        exit 0
    }
}

function Build-DockerImages {
    Write-ColorOutput "`nBuilding and pushing Docker images..." "Yellow"
    
    # Get ECR login
    $password = aws ecr get-login-password --region ap-south-1
    $password | docker login --username AWS --password-stdin "$($script:ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com"
    
    $images = @("mcp-server", "chat-ui", "admin-ui", "mock-api")
    
    foreach ($image in $images) {
        Write-ColorOutput "`nBuilding $image..." "Yellow"
        
        $tag = "$($script:ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev/${image}:latest"
        
        switch ($image) {
            "mcp-server" { docker build -t $tag -f ../../mcp-server/Dockerfile ../../mcp-server }
            "chat-ui" { docker build -t $tag -f ../../chat-ui/Dockerfile ../../chat-ui }
            "admin-ui" { docker build -t $tag -f ../../admin-ui/Dockerfile ../../admin-ui }
            "mock-api" { docker build -t $tag -f ../../mock-api/Dockerfile ../../mock-api }
        }
        
        Write-ColorOutput "Pushing $image..." "Yellow"
        docker push $tag
    }
    
    Write-ColorOutput "All images pushed!" "Green"
}

function Show-Outputs {
    Write-ColorOutput "`nDeployment outputs:" "Yellow"
    terraform output
}

# Main execution
switch ($Command) {
    "init" {
        Test-Prerequisites
        Test-AWSCredentials
        Initialize-Backend
        Initialize-Terraform
    }
    "plan" {
        Test-TfVars
        New-DeploymentPlan
    }
    "apply" {
        Invoke-Deployment
    }
    "deploy" {
        Test-Prerequisites
        Test-AWSCredentials
        Test-TfVars
        Initialize-Backend
        Initialize-Terraform
        Test-TerraformConfig
        New-DeploymentPlan
        Invoke-Deployment
        Show-Outputs
    }
    "images" {
        Test-Prerequisites
        Test-AWSCredentials
        Build-DockerImages
    }
    "destroy" {
        Write-ColorOutput "WARNING: This will destroy all infrastructure!" "Red"
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            terraform destroy
        }
    }
    "outputs" {
        Show-Outputs
    }
}
