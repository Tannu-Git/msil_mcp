"""
Response Shaper - Optimize API responses for token efficiency
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResponseConfig:
    """Configuration for response shaping"""
    include_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    max_array_size: Optional[int] = None
    compact: bool = True
    max_depth: int = 10


class ResponseShaper:
    """Shape API responses for token efficiency"""
    
    def shape(
        self,
        response: Dict[str, Any],
        config: Optional[ResponseConfig] = None
    ) -> Dict[str, Any]:
        """
        Apply response shaping rules
        
        Args:
            response: Original API response
            config: Shaping configuration
            
        Returns:
            Shaped response optimized for tokens
        """
        if not config:
            config = ResponseConfig()
        
        shaped = response
        
        # Include only specified fields (whitelist)
        if config.include_fields:
            shaped = self._include_fields(shaped, config.include_fields)
        
        # Exclude specified fields (blacklist)
        if config.exclude_fields:
            shaped = self._exclude_fields(shaped, config.exclude_fields)
        
        # Limit array sizes
        if config.max_array_size:
            shaped = self._limit_arrays(shaped, config.max_array_size)
        
        # Compact: remove nulls and empty objects
        if config.compact:
            shaped = self._compact(shaped)
        
        return shaped
    
    def _include_fields(self, data: Any, fields: List[str], depth: int = 0) -> Any:
        """Include only specified fields (supports dot notation)"""
        if depth > 10:  # Prevent infinite recursion
            return data
        
        if isinstance(data, dict):
            result = {}
            for field in fields:
                if '.' in field:
                    # Nested field: address.city
                    parent, child = field.split('.', 1)
                    if parent in data:
                        if parent not in result:
                            result[parent] = {}
                        result[parent] = self._include_fields(
                            data[parent], 
                            [child],
                            depth + 1
                        )
                else:
                    # Top-level field
                    if field in data:
                        result[field] = data[field]
            return result
        elif isinstance(data, list):
            return [self._include_fields(item, fields, depth + 1) for item in data]
        return data
    
    def _exclude_fields(self, data: Any, fields: List[str], depth: int = 0) -> Any:
        """Exclude specified fields recursively"""
        if depth > 10:
            return data
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Skip excluded fields
                if key in fields:
                    continue
                
                # Recursively exclude from nested objects
                if isinstance(value, (dict, list)):
                    result[key] = self._exclude_fields(value, fields, depth + 1)
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._exclude_fields(item, fields, depth + 1) for item in data]
        return data
    
    def _limit_arrays(self, data: Any, max_size: int, depth: int = 0) -> Any:
        """Limit array sizes to reduce token usage"""
        if depth > 10:
            return data
        
        if isinstance(data, list):
            limited = data[:max_size]
            if len(data) > max_size:
                logger.debug(f"Array truncated from {len(data)} to {max_size} items")
            return [self._limit_arrays(item, max_size, depth + 1) for item in limited]
        elif isinstance(data, dict):
            return {
                k: self._limit_arrays(v, max_size, depth + 1) 
                for k, v in data.items()
            }
        return data
    
    def _compact(self, data: Any, depth: int = 0) -> Any:
        """Remove null values, empty objects, and empty arrays"""
        if depth > 10:
            return data
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Skip None values
                if value is None:
                    continue
                
                # Recursively compact nested structures
                if isinstance(value, (dict, list)):
                    compacted = self._compact(value, depth + 1)
                    # Skip empty objects and arrays
                    if compacted or compacted == 0 or compacted is False:
                        result[key] = compacted
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, (dict, list)):
                    compacted = self._compact(item, depth + 1)
                    if compacted or compacted == 0 or compacted is False:
                        result.append(compacted)
                elif item is not None:
                    result.append(item)
            return result
        return data
    
    def estimate_token_count(self, data: Dict[str, Any]) -> int:
        """
        Rough estimate of token count for response
        Rule of thumb: ~4 characters per token
        """
        import json
        json_str = json.dumps(data)
        return len(json_str) // 4


# Singleton instance
response_shaper = ResponseShaper()
