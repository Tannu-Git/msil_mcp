"""S3 WORM (Write-Once-Read-Many) audit storage."""
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class S3WORMStore:
    """Write-Once-Read-Many audit log storage using S3 Object Lock."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = "ap-south-1",
        retention_days: int = 365,
        object_lock_mode: str = "GOVERNANCE"
    ):
        """
        Initialize S3 WORM store.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            retention_days: Days to retain audit logs
            object_lock_mode: GOVERNANCE or COMPLIANCE
        """
        self.bucket_name = bucket_name
        self.retention_days = retention_days
        self.object_lock_mode = object_lock_mode
        
        try:
            self.s3_client = boto3.client('s3', region_name=region)
            logger.info(f"Initialized S3 WORM store: bucket={bucket_name}, region={region}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    async def write_audit_event(self, event: Dict[str, Any]) -> str:
        """
        Write audit event to S3 with Object Lock.
        
        Args:
            event: Audit event dictionary
            
        Returns:
            S3 object key
        """
        try:
            # Create immutable object key with date partitioning
            key = self._generate_key(event)
            
            # Serialize event
            event_data = self._serialize_event(event)
            
            # Calculate checksum for integrity
            checksum = self._calculate_checksum(event_data)
            
            # Calculate retention until date
            retention_until = datetime.utcnow() + timedelta(days=self.retention_days)
            
            # Write to S3 with Object Lock
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=event_data,
                ContentType='application/json',
                ObjectLockMode=self.object_lock_mode,
                ObjectLockRetainUntilDate=retention_until,
                Metadata={
                    'event_id': str(event.get('event_id', '')),
                    'event_type': event.get('event_type', ''),
                    'checksum': checksum,
                    'retention_until': retention_until.isoformat()
                }
            )
            
            logger.info(f"Wrote audit event to S3: {key} (retention until {retention_until})")
            return key
            
        except Exception as e:
            logger.error(f"Failed to write audit event to S3: {e}")
            raise
    
    def _generate_key(self, event: Dict[str, Any]) -> str:
        """
        Generate S3 key with date partitioning.
        
        Format: audit-logs/year=YYYY/month=MM/day=DD/{event_id}.json
        """
        timestamp = event.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()
        
        event_id = event.get('event_id', 'unknown')
        
        return (
            f"audit-logs/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"{event_id}.json"
        )
    
    def _serialize_event(self, event: Dict[str, Any]) -> str:
        """Serialize event to JSON."""
        # Convert datetime objects to ISO format
        serializable_event = {}
        for key, value in event.items():
            if isinstance(value, datetime):
                serializable_event[key] = value.isoformat()
            else:
                serializable_event[key] = value
        
        return json.dumps(serializable_event, indent=2)
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA-256 checksum for integrity."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def verify_integrity(self, key: str) -> bool:
        """
        Verify audit log hasn't been tampered.
        
        Args:
            key: S3 object key
            
        Returns:
            True if integrity check passes, False otherwise
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            data = response['Body'].read().decode()
            expected_checksum = response['Metadata'].get('checksum')
            actual_checksum = self._calculate_checksum(data)
            
            if expected_checksum == actual_checksum:
                logger.info(f"Integrity check passed for {key}")
                return True
            else:
                logger.error(f"Integrity check FAILED for {key}: expected={expected_checksum}, actual={actual_checksum}")
                return False
                
        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False
    
    async def read_audit_event(self, key: str) -> Dict[str, Any]:
        """
        Read audit event from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Audit event dictionary
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            data = response['Body'].read().decode()
            event = json.loads(data)
            
            logger.debug(f"Read audit event from S3: {key}")
            return event
            
        except Exception as e:
            logger.error(f"Failed to read audit event from S3: {e}")
            raise
    
    async def query_events(
        self,
        year: int,
        month: int,
        day: int,
        max_keys: int = 1000
    ) -> list:
        """
        Query audit events for a specific date.
        
        Args:
            year: Year
            month: Month (1-12)
            day: Day (1-31)
            max_keys: Maximum number of keys to return
            
        Returns:
            List of S3 object keys
        """
        prefix = f"audit-logs/year={year}/month={month:02d}/day={day:02d}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            keys = [obj['Key'] for obj in response.get('Contents', [])]
            logger.info(f"Found {len(keys)} audit events for {year}-{month:02d}-{day:02d}")
            return keys
            
        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []
    
    def get_object_lock_status(self, key: str) -> Dict[str, Any]:
        """
        Get Object Lock status for an audit log.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary with lock status
        """
        try:
            response = self.s3_client.get_object_retention(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return {
                "mode": response['Retention']['Mode'],
                "retain_until_date": response['Retention']['RetainUntilDate'].isoformat()
            }
        except self.s3_client.exceptions.NoSuchObjectLockConfiguration:
            return {"mode": None, "retain_until_date": None}
        except Exception as e:
            logger.error(f"Failed to get object lock status: {e}")
            return {"error": str(e)}
