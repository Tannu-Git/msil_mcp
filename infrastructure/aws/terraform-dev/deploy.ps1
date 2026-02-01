# MSIL MCP Server - Minimal Dev Deployment Script (PowerShell)
# =============================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("init", "plan", "apply", "deploy", "images", "destroy", "ssh", "logs", "status")]
    [string]$Command = "deploy"
)

$ErrorActionPreference = "Stop"
$REGION = "ap-south-1"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "============================================" "Green"
Write-ColorOutput "   MSIL MCP Server - Minimal Dev Deploy" "Green"
Write-ColorOutput "============================================" "Green"

function Get-InstanceInfo {
    $instanceId = terraform output -raw instance_id 2>$null
    $publicIp = terraform output -raw instance_public_ip 2>$null
    return @{
        InstanceId = $instanceId
        PublicIp = $publicIp
    }
}

function Initialize-Terraform {
    Write-ColorOutput "`nInitializing Terraform..." "Yellow"
    terraform init
    Write-ColorOutput "Done!" "Green"
}

function New-DeploymentPlan {
    Write-ColorOutput "`nCreating deployment plan..." "Yellow"
    terraform plan -out=tfplan
    Write-ColorOutput "Done!" "Green"
}

function Invoke-Deployment {
    Write-ColorOutput "`nApplying deployment..." "Yellow"
    terraform apply tfplan
    Write-ColorOutput "`nDeployment complete!" "Green"
    
    Write-ColorOutput "`n============================================" "Cyan"
    Write-ColorOutput "   ACCESS URLs" "Cyan"
    Write-ColorOutput "============================================" "Cyan"
    terraform output
}

function Build-DockerImages {
    Write-ColorOutput "`nBuilding and pushing Docker images..." "Yellow"
    
    $accountId = aws sts get-caller-identity --query Account --output text
    $ecrBase = "$accountId.dkr.ecr.$REGION.amazonaws.com/msil-mcp-dev"
    
    # ECR Login
    $password = aws ecr get-login-password --region $REGION
    $password | docker login --username AWS --password-stdin "$accountId.dkr.ecr.$REGION.amazonaws.com"
    
    $services = @(
        @{ Name = "mcp-server"; Path = "../../../mcp-server"; Dockerfile = "Dockerfile" },
        @{ Name = "chat-ui"; Path = "../../../chat-ui"; Dockerfile = "Dockerfile" },
        @{ Name = "admin-ui"; Path = "../../../admin-ui"; Dockerfile = "Dockerfile" },
        @{ Name = "mock-api"; Path = "../../../mock-api"; Dockerfile = "Dockerfile" }
    )
    
    foreach ($svc in $services) {
        Write-ColorOutput "`nBuilding $($svc.Name)..." "Yellow"
        $tag = "$ecrBase/$($svc.Name):latest"
        
        Push-Location $svc.Path
        docker build -t $tag -f $svc.Dockerfile .
        docker push $tag
        Pop-Location
        
        Write-ColorOutput "Pushed $($svc.Name)" "Green"
    }
    
    Write-ColorOutput "`nAll images pushed! Restarting services on EC2..." "Yellow"
    
    $info = Get-InstanceInfo
    if ($info.InstanceId) {
        aws ssm send-command `
            --instance-ids $info.InstanceId `
            --document-name "AWS-RunShellScript" `
            --parameters 'commands=["cd /opt/msil-mcp && docker-compose pull && docker-compose up -d"]' `
            --region $REGION
        Write-ColorOutput "Restart command sent!" "Green"
    }
}

function Connect-SSH {
    $info = Get-InstanceInfo
    if ($info.InstanceId) {
        Write-ColorOutput "Connecting via SSM Session Manager..." "Yellow"
        aws ssm start-session --target $info.InstanceId --region $REGION
    } else {
        Write-ColorOutput "No instance found. Deploy first." "Red"
    }
}

function Get-Logs {
    $info = Get-InstanceInfo
    if ($info.InstanceId) {
        Write-ColorOutput "Fetching logs..." "Yellow"
        aws ssm send-command `
            --instance-ids $info.InstanceId `
            --document-name "AWS-RunShellScript" `
            --parameters 'commands=["cd /opt/msil-mcp && docker-compose logs --tail=100"]' `
            --output text `
            --region $REGION
    }
}

function Get-Status {
    $info = Get-InstanceInfo
    Write-ColorOutput "`n============================================" "Cyan"
    Write-ColorOutput "   INSTANCE STATUS" "Cyan"
    Write-ColorOutput "============================================" "Cyan"
    
    if ($info.InstanceId) {
        Write-ColorOutput "Instance ID: $($info.InstanceId)" "White"
        Write-ColorOutput "Public IP:   $($info.PublicIp)" "White"
        
        $state = aws ec2 describe-instances `
            --instance-ids $info.InstanceId `
            --query 'Reservations[0].Instances[0].State.Name' `
            --output text `
            --region $REGION
        
        Write-ColorOutput "State:       $state" $(if ($state -eq "running") { "Green" } else { "Yellow" })
        
        Write-ColorOutput "`nURLs:" "Cyan"
        Write-ColorOutput "  MCP Server: http://$($info.PublicIp):8000" "White"
        Write-ColorOutput "  Chat UI:    http://$($info.PublicIp):3001" "White"
        Write-ColorOutput "  Admin UI:   http://$($info.PublicIp):3002" "White"
        Write-ColorOutput "  Mock API:   http://$($info.PublicIp):3000" "White"
    } else {
        Write-ColorOutput "No instance deployed yet." "Yellow"
    }
}

# Main execution
switch ($Command) {
    "init" {
        Initialize-Terraform
    }
    "plan" {
        New-DeploymentPlan
    }
    "apply" {
        Invoke-Deployment
    }
    "deploy" {
        Initialize-Terraform
        New-DeploymentPlan
        Invoke-Deployment
    }
    "images" {
        Build-DockerImages
    }
    "destroy" {
        Write-ColorOutput "WARNING: This will destroy all dev infrastructure!" "Red"
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            terraform destroy -auto-approve
        }
    }
    "ssh" {
        Connect-SSH
    }
    "logs" {
        Get-Logs
    }
    "status" {
        Get-Status
    }
}
