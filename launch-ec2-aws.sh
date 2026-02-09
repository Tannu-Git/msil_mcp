#!/bin/bash
################################################################################
# AWS EC2 Launcher for MSIL MCP Server
# Run this from your local machine to provision EC2 instance
# Requirements: AWS CLI configured with credentials
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

################################################################################
# Configuration
################################################################################
INSTANCE_NAME="msil-mcp-demo"
INSTANCE_TYPE="t4g.nano"
REGION="ap-northeast-1"  # Tokyo (adjust as needed)
KEY_PAIR_NAME="msil-mcp-key"
VOLUME_SIZE="40"  # EBS volume size in GB
VOLUME_TYPE="gp3"

log "=== AWS EC2 Instance Provisioning ==="
log "Region: $REGION"
log "Instance Type: $INSTANCE_TYPE"
log "Volume: $VOLUME_SIZE GB $VOLUME_TYPE"

################################################################################
# Check AWS CLI
################################################################################
if ! command -v aws &> /dev/null; then
    error "AWS CLI not installed. Install from: https://aws.amazon.com/cli/"
fi

log "AWS CLI found: $(aws --version)"

################################################################################
# Check/Create Key Pair
################################################################################
log "Checking for key pair: $KEY_PAIR_NAME"

if aws ec2 describe-key-pairs --key-names "$KEY_PAIR_NAME" --region "$REGION" > /dev/null 2>&1; then
    success "Key pair already exists"
else
    log "Creating key pair..."
    aws ec2 create-key-pair \
        --key-name "$KEY_PAIR_NAME" \
        --region "$REGION" \
        --query 'KeyMaterial' \
        --output text > "${KEY_PAIR_NAME}.pem"
    
    chmod 400 "${KEY_PAIR_NAME}.pem"
    success "Key pair created: ${KEY_PAIR_NAME}.pem"
fi

################################################################################
# Get Latest Amazon Linux 2 AMI
################################################################################
log "Finding latest Amazon Linux 2 AMI for arm64..."

AMI_ID=$(aws ec2 describe-images \
    --region "$REGION" \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-arm64-gp2" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)

[ -z "$AMI_ID" ] && error "Could not find Amazon Linux 2 AMI"
success "Using AMI: $AMI_ID"

################################################################################
# Create Security Group
################################################################################
SG_NAME="msil-mcp-sg"
log "Checking security group: $SG_NAME"

SG_ID=$(aws ec2 describe-security-groups \
    --region "$REGION" \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    log "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Security group for MSIL MCP Server" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text)
    
    # Allow SSH
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp --port 22 --cidr 0.0.0.0/0 \
        --region "$REGION" > /dev/null
    
    # Allow HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 \
        --region "$REGION" > /dev/null
    
    # Allow HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 \
        --region "$REGION" > /dev/null
    
    success "Security group created: $SG_ID"
else
    success "Using existing security group: $SG_ID"
fi

################################################################################
# Launch EC2 Instance
################################################################################
log "Launching EC2 instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_PAIR_NAME" \
    --security-group-ids "$SG_ID" \
    --region "$REGION" \
    --block-device-mappings "DeviceName=/dev/xvda,Ebs={VolumeSize=20,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

[ -z "$INSTANCE_ID" ] && error "Failed to launch instance"
success "Instance launched: $INSTANCE_ID"

log "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
success "Instance is running"

################################################################################
# Create and Attach EBS Volume
################################################################################
log "Creating EBS volume ($VOLUME_SIZE GB $VOLUME_TYPE)..."

AZ=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' \
    --output text)

VOLUME_ID=$(aws ec2 create-volume \
    --availability-zone "$AZ" \
    --size "$VOLUME_SIZE" \
    --volume-type "$VOLUME_TYPE" \
    --region "$REGION" \
    --tag-specifications "ResourceType=volume,Tags=[{Key=Name,Value=$INSTANCE_NAME-data}]" \
    --query 'VolumeId' \
    --output text)

[ -z "$VOLUME_ID" ] && error "Failed to create EBS volume"
success "EBS volume created: $VOLUME_ID"

log "Waiting for volume to be available..."
aws ec2 wait volume-available --volume-ids "$VOLUME_ID" --region "$REGION"
success "Volume is available"

log "Attaching volume to instance..."
aws ec2 attach-volume \
    --volume-id "$VOLUME_ID" \
    --instance-id "$INSTANCE_ID" \
    --device /dev/sdb \
    --region "$REGION" > /dev/null

success "Volume attached as /dev/sdb"

################################################################################
# Get Instance Details
################################################################################
log "Retrieving instance details..."
sleep 5

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

PRIVATE_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
    --output text)

################################################################################
# Create User Data Script (runs when instance starts)
################################################################################
cat > /tmp/user-data.sh << 'USERDATA'
#!/bin/bash
# Format and mount EBS volume
set -e

# Wait for volume to be attached
sleep 10

# Format EBS volume
sudo mkfs -t ext4 /dev/nvme1n1 || echo "Volume may already be formatted"

# Create mount point
sudo mkdir -p /data

# Mount volume
sudo mount /dev/nvme1n1 /data

# Add to fstab for persistent mounting
echo '/dev/nvme1n1 /data ext4 defaults,nofail 0 0' | sudo tee -a /etc/fstab

# Set permissions
sudo chown -R ec2-user:ec2-user /data

# Create subdirectories
mkdir -p /data/{app,db,logs}

# Clone repository to /data
cd /data/app
git clone https://github.com/Tannu-Git/msil_mcp.git . || echo "Directory exists"

# Execute deployment script
chmod +x /data/app/deploy-aws-ec2.sh
/data/app/deploy-aws-ec2.sh

USERDATA

################################################################################
# Display Information
################################################################################
echo ""
echo -e "${GREEN}=== EC2 INSTANCE PROVISIONED ===${NC}"
echo ""
echo -e "📍 ${BLUE}Instance Details${NC}"
echo "   Instance ID: $INSTANCE_ID"
echo "   Key Pair: $KEY_PAIR_NAME"
echo "   Region: $REGION"
echo "   Availability Zone: $AZ"
echo ""
echo -e "🌐 ${BLUE}Network${NC}"
echo "   Public IP: $PUBLIC_IP"
echo "   Private IP: $PRIVATE_IP"
echo "   Security Group: $SG_ID"
echo ""
echo -e "💾 ${BLUE}Storage${NC}"
echo "   Root Volume: 20GB (gp3)"
echo "   Data Volume: $VOLUME_SIZE GB (gp3, attached as /dev/sdb)"
echo ""
echo -e "🔑 ${BLUE}SSH Access${NC}"
echo "   Command: ssh -i ${KEY_PAIR_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo -e "📦 ${BLUE}Deployment${NC}"
echo "   Deployment script: /data/app/deploy-aws-ec2.sh"
echo "   Or run manually: cd /data/app && ./deploy-aws-ec2.sh"
echo ""
echo -e "⏰ ${BLUE}Next Steps${NC}"
echo "   1. Wait 2-3 minutes for deployment to complete"
echo "   2. SSH into instance and monitor:"
echo "      ssh -i ${KEY_PAIR_NAME}.pem ec2-user@$PUBLIC_IP"
echo "      tail -f /data/logs/deployment.log"
echo "   3. Once complete, access:"
echo "      Admin UI: https://$PUBLIC_IP/admin"
echo "      Chat UI: https://$PUBLIC_IP/chat"
echo ""
echo -e "💰 ${BLUE}Estimated Costs${NC}"
echo "   t4g.nano: \$2.81/month"
echo "   EBS $VOLUME_SIZE GB: \$4-5/month"
echo "   Total: ~\$7-8/month"
echo ""
echo -e "⚠️  ${YELLOW}Important${NC}"
echo "   • Keep ${KEY_PAIR_NAME}.pem safe!"
echo "   • Self-signed SSL cert (browser warning is normal)"
echo "   • For production: Use ACM certificate"
echo ""

success "Setup complete! Deployment will start automatically..."
