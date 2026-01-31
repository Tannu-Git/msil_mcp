"""
OpenAPI Parser Module
Converts OpenAPI/Swagger specifications into MCP Tool definitions
"""
import logging
import uuid
import yaml
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAPIParser:
    """Parse OpenAPI 3.x and Swagger 2.0 specifications"""
    
    def __init__(self):
        self.spec_version = None
        self.spec_data = None
    
    def parse(self, content: str, format: str = "yaml") -> Dict[str, Any]:
        """
        Parse OpenAPI specification content
        
        Args:
            content: Raw OpenAPI spec content
            format: 'yaml' or 'json'
            
        Returns:
            Parsed spec data and metadata
        """
        try:
            if format == "yaml":
                self.spec_data = yaml.safe_load(content)
            else:
                self.spec_data = json.loads(content)
            
            # Detect version
            if "openapi" in self.spec_data:
                self.spec_version = self.spec_data["openapi"]
            elif "swagger" in self.spec_data:
                self.spec_version = f"swagger_{self.spec_data['swagger']}"
            else:
                raise ValueError("Unknown spec format - missing 'openapi' or 'swagger' field")
            
            logger.info(f"Parsed OpenAPI spec version: {self.spec_version}")
            
            return {
                "version": self.spec_version,
                "title": self.spec_data.get("info", {}).get("title", "Unknown API"),
                "description": self.spec_data.get("info", {}).get("description", ""),
                "spec_version": self.spec_data.get("info", {}).get("version", "1.0.0"),
                "base_path": self._extract_base_path(),
                "servers": self.spec_data.get("servers", []),
                "paths_count": len(self.spec_data.get("paths", {}))
            }
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            raise ValueError(f"Failed to parse spec: {str(e)}")
    
    def _extract_base_path(self) -> str:
        """Extract base path from spec"""
        if "servers" in self.spec_data and self.spec_data["servers"]:
            return self.spec_data["servers"][0].get("url", "")
        elif "basePath" in self.spec_data:
            return self.spec_data["basePath"]
        return ""
    
    def generate_tools(self, 
                      category: str = "imported",
                      bundle_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate MCP tool definitions from OpenAPI spec
        
        Args:
            category: Tool category (e.g., 'customer', 'vehicle')
            bundle_name: Optional bundle name for grouping
            
        Returns:
            List of tool definitions
        """
        if not self.spec_data:
            raise ValueError("No spec data loaded. Call parse() first.")
        
        tools = []
        paths = self.spec_data.get("paths", {})
        
        for path, path_item in paths.items():
            # Process each HTTP method
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    operation = path_item[method]
                    tool = self._create_tool_from_operation(
                        path, method, operation, category, bundle_name
                    )
                    if tool:
                        tools.append(tool)
        
        logger.info(f"Generated {len(tools)} tools from OpenAPI spec")
        return tools
    
    def _create_tool_from_operation(self,
                                    path: str,
                                    method: str,
                                    operation: Dict[str, Any],
                                    category: str,
                                    bundle_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """Create a single tool definition from OpenAPI operation"""
        
        # Generate tool name from operationId or path
        tool_name = operation.get("operationId")
        if not tool_name:
            # Generate from path: /api/customer/resolve -> resolve_customer
            tool_name = self._generate_tool_name(path, method)
        
        # Extract description
        description = operation.get("summary") or operation.get("description") or f"{method.upper()} {path}"
        
        # Generate input schema from parameters
        input_schema = self._generate_input_schema(operation)
        
        # Create tool definition
        tool = {
            "id": str(uuid.uuid4()),
            "name": tool_name,
            "display_name": self._humanize_name(tool_name),
            "description": description,
            "category": category,
            "bundle_name": bundle_name,
            "api_endpoint": path,
            "http_method": method.upper(),
            "input_schema": input_schema,
            "is_active": True,
            "version": self.spec_data.get("info", {}).get("version", "1.0.0"),
            "source": "openapi_import",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return tool
    
    def _generate_tool_name(self, path: str, method: str) -> str:
        """
        Generate tool name from path and method
        Examples:
            POST /api/customer/resolve -> resolve_customer
            GET /api/dealers/nearby -> get_nearby_dealers
        """
        # Remove base path and split
        parts = [p for p in path.split("/") if p and p != "api"]
        
        # Add method as prefix for GET/DELETE
        if method in ["get", "delete"]:
            parts.insert(0, method)
        
        # Join with underscores
        name = "_".join(parts).lower()
        
        # Remove special characters
        name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        
        return name
    
    def _humanize_name(self, name: str) -> str:
        """Convert snake_case to Title Case"""
        return " ".join(word.capitalize() for word in name.split("_"))
    
    def _generate_input_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON Schema for tool inputs from OpenAPI parameters
        Combines path params, query params, and request body
        """
        properties = {}
        required = []
        
        # Process parameters (path, query, header)
        parameters = operation.get("parameters", [])
        for param in parameters:
            if param.get("in") in ["path", "query"]:
                param_name = param["name"]
                param_schema = self._convert_param_to_schema(param)
                properties[param_name] = param_schema
                
                if param.get("required", False):
                    required.append(param_name)
        
        # Process request body (OpenAPI 3.x)
        if "requestBody" in operation:
            body_schema = self._extract_request_body_schema(operation["requestBody"])
            if body_schema:
                # Merge body properties
                if "properties" in body_schema:
                    properties.update(body_schema["properties"])
                if "required" in body_schema:
                    required.extend(body_schema["required"])
        
        # Fallback: create minimal schema
        if not properties:
            properties = {
                "data": {
                    "type": "object",
                    "description": "Request data"
                }
            }
        
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = list(set(required))  # Remove duplicates
        
        return schema
    
    def _convert_param_to_schema(self, param: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI parameter to JSON Schema property"""
        schema = {}
        
        # OpenAPI 3.x: schema is nested
        if "schema" in param:
            schema = param["schema"].copy()
        else:
            # Swagger 2.0: type is direct
            schema["type"] = param.get("type", "string")
            if "format" in param:
                schema["format"] = param["format"]
            if "enum" in param:
                schema["enum"] = param["enum"]
        
        # Add description
        if "description" in param:
            schema["description"] = param["description"]
        
        return schema
    
    def _extract_request_body_schema(self, request_body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract schema from OpenAPI 3.x requestBody"""
        try:
            content = request_body.get("content", {})
            
            # Try JSON content first
            for content_type in ["application/json", "application/x-www-form-urlencoded", "*/*"]:
                if content_type in content:
                    media_type = content[content_type]
                    if "schema" in media_type:
                        return self._resolve_schema_ref(media_type["schema"])
            
            return None
        except Exception as e:
            logger.warning(f"Failed to extract request body schema: {e}")
            return None
    
    def _resolve_schema_ref(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve $ref references in schema (simplified)"""
        if "$ref" in schema:
            # Extract ref path: #/components/schemas/Customer
            ref_path = schema["$ref"].split("/")
            
            # Navigate to referenced schema
            ref_schema = self.spec_data
            for part in ref_path[1:]:  # Skip '#'
                ref_schema = ref_schema.get(part, {})
            
            return ref_schema.copy() if ref_schema else schema
        
        return schema
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate generated tools
        
        Returns:
            Tuple of (valid_tools, error_messages)
        """
        valid_tools = []
        errors = []
        
        for tool in tools:
            try:
                # Check required fields
                required_fields = ["name", "description", "api_endpoint", "http_method", "input_schema"]
                missing = [f for f in required_fields if not tool.get(f)]
                
                if missing:
                    errors.append(f"Tool '{tool.get('name', 'unknown')}' missing fields: {', '.join(missing)}")
                    continue
                
                # Validate input schema
                schema = tool["input_schema"]
                if not isinstance(schema, dict) or "type" not in schema:
                    errors.append(f"Tool '{tool['name']}' has invalid input schema")
                    continue
                
                valid_tools.append(tool)
                
            except Exception as e:
                errors.append(f"Validation error for tool: {str(e)}")
        
        logger.info(f"Validated {len(valid_tools)}/{len(tools)} tools")
        if errors:
            logger.warning(f"Validation errors: {errors}")
        
        return valid_tools, errors


def parse_openapi_spec(content: str, format: str = "yaml") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Convenience function to parse OpenAPI and generate tools
    
    Args:
        content: OpenAPI spec content
        format: 'yaml' or 'json'
        
    Returns:
        Tuple of (spec_metadata, tools_list)
    """
    parser = OpenAPIParser()
    metadata = parser.parse(content, format)
    tools = parser.generate_tools()
    valid_tools, errors = parser.validate_tools(tools)
    
    return metadata, valid_tools
