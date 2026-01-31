"""
OpenAPI Import API Endpoints
Handles uploading, parsing, and registering tools from OpenAPI specs
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.openapi.parser import OpenAPIParser
from app.core.tools.registry import tool_registry, Tool

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class OpenAPISpec(BaseModel):
    """OpenAPI specification metadata"""
    id: str
    name: str
    version: str
    description: str
    uploaded_at: str
    tools_generated: int
    status: str  # 'parsed', 'preview', 'approved'


class ToolPreview(BaseModel):
    """Preview of a tool generated from OpenAPI"""
    id: str
    name: str
    display_name: str
    description: str
    category: str
    api_endpoint: str
    http_method: str
    input_schema: Dict[str, Any]
    is_active: bool = True


class ImportRequest(BaseModel):
    """Request to import OpenAPI spec"""
    category: str = "imported"
    bundle_name: Optional[str] = None
    auto_approve: bool = False


class ApproveToolsRequest(BaseModel):
    """Request to approve and register tools"""
    spec_id: str
    tool_ids: List[str]  # Which tools to actually register
    category: Optional[str] = None


# ============================================
# In-Memory Storage (MVP - replace with DB later)
# ============================================

# Store parsed specs temporarily
_specs_cache: Dict[str, Dict[str, Any]] = {}


# ============================================
# API Endpoints
# ============================================

@router.post("/upload")
async def upload_openapi_spec(
    file: UploadFile = File(...),
    category: str = Form("imported"),
    bundle_name: Optional[str] = Form(None)
) -> JSONResponse:
    """
    Upload and parse OpenAPI specification file
    
    Supports:
    - OpenAPI 3.0, 3.1
    - Swagger 2.0
    - YAML or JSON format
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode("utf-8")
        
        # Detect format from filename
        file_format = "yaml" if file.filename.endswith((".yaml", ".yml")) else "json"
        
        # Parse OpenAPI spec
        parser = OpenAPIParser()
        metadata = parser.parse(content_str, format=file_format)
        
        # Generate tools
        tools = parser.generate_tools(category=category, bundle_name=bundle_name)
        valid_tools, errors = parser.validate_tools(tools)
        
        # Generate spec ID
        spec_id = str(uuid.uuid4())
        
        # Store in cache
        _specs_cache[spec_id] = {
            "id": spec_id,
            "filename": file.filename,
            "metadata": metadata,
            "tools": valid_tools,
            "errors": errors,
            "content": content_str,
            "format": file_format,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "parsed"
        }
        
        logger.info(f"Uploaded OpenAPI spec: {file.filename} → {len(valid_tools)} tools")
        
        return JSONResponse({
            "spec_id": spec_id,
            "name": metadata["title"],
            "version": metadata["spec_version"],
            "description": metadata.get("description", ""),
            "tools_generated": len(valid_tools),
            "tools": valid_tools,
            "errors": errors,
            "status": "success"
        })
        
    except ValueError as e:
        logger.error(f"OpenAPI parsing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process spec: {str(e)}")


@router.post("/import-url")
async def import_from_url(
    url: str,
    category: str = "imported",
    bundle_name: Optional[str] = None
) -> JSONResponse:
    """Import OpenAPI spec from URL"""
    try:
        import httpx
        
        # Fetch from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            content = response.text
        
        # Detect format
        file_format = "yaml" if url.endswith((".yaml", ".yml")) else "json"
        
        # Parse
        parser = OpenAPIParser()
        metadata = parser.parse(content, format=file_format)
        tools = parser.generate_tools(category=category, bundle_name=bundle_name)
        valid_tools, errors = parser.validate_tools(tools)
        
        # Store
        spec_id = str(uuid.uuid4())
        _specs_cache[spec_id] = {
            "id": spec_id,
            "url": url,
            "metadata": metadata,
            "tools": valid_tools,
            "errors": errors,
            "content": content,
            "format": file_format,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "parsed"
        }
        
        logger.info(f"Imported OpenAPI from URL: {url} → {len(valid_tools)} tools")
        
        return JSONResponse({
            "spec_id": spec_id,
            "name": metadata["title"],
            "version": metadata["spec_version"],
            "tools_generated": len(valid_tools),
            "tools": valid_tools,
            "errors": errors,
            "status": "success"
        })
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        logger.error(f"URL import error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/specs")
async def list_specs() -> List[OpenAPISpec]:
    """List all uploaded OpenAPI specs"""
    specs = []
    for spec_id, spec_data in _specs_cache.items():
        specs.append(OpenAPISpec(
            id=spec_id,
            name=spec_data["metadata"]["title"],
            version=spec_data["metadata"]["spec_version"],
            description=spec_data["metadata"].get("description", ""),
            uploaded_at=spec_data["uploaded_at"],
            tools_generated=len(spec_data["tools"]),
            status=spec_data["status"]
        ))
    return specs


@router.get("/preview/{spec_id}")
async def preview_tools(spec_id: str) -> Dict[str, Any]:
    """
    Preview tools generated from a spec
    Allows editing before approval
    """
    if spec_id not in _specs_cache:
        raise HTTPException(status_code=404, detail="Spec not found")
    
    spec_data = _specs_cache[spec_id]
    
    return {
        "spec_id": spec_id,
        "spec_name": spec_data["metadata"]["title"],
        "spec_version": spec_data["metadata"]["spec_version"],
        "tools": spec_data["tools"],
        "errors": spec_data.get("errors", []),
        "status": spec_data["status"]
    }


@router.post("/approve")
async def approve_and_register_tools(request: ApproveToolsRequest) -> JSONResponse:
    """
    Approve tools and register them in the tool registry
    Makes tools available via MCP protocol immediately
    """
    try:
        if request.spec_id not in _specs_cache:
            raise HTTPException(status_code=404, detail="Spec not found")
        
        spec_data = _specs_cache[request.spec_id]
        tools_to_register = []
        
        # Filter tools by requested IDs
        for tool_data in spec_data["tools"]:
            if tool_data["id"] in request.tool_ids:
                # Override category if provided
                if request.category:
                    tool_data["category"] = request.category
                
                # Create Tool object
                tool = Tool(
                    id=uuid.UUID(tool_data["id"]),
                    name=tool_data["name"],
                    display_name=tool_data["display_name"],
                    description=tool_data["description"],
                    category=tool_data["category"],
                    api_endpoint=tool_data["api_endpoint"],
                    http_method=tool_data["http_method"],
                    input_schema=tool_data["input_schema"],
                    is_active=True,
                    version=tool_data.get("version", "1.0.0"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                tools_to_register.append(tool)
        
        # Register tools
        registered_count = 0
        for tool in tools_to_register:
            await tool_registry.register_tool(tool)
            registered_count += 1
        
        # Update spec status
        spec_data["status"] = "approved"
        
        logger.info(f"Registered {registered_count} tools from spec {request.spec_id}")
        
        return JSONResponse({
            "status": "success",
            "message": f"Registered {registered_count} tools",
            "tools_registered": registered_count,
            "tool_names": [t.name for t in tools_to_register]
        })
        
    except Exception as e:
        logger.error(f"Tool registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tools/{tool_id}")
async def update_tool_preview(
    tool_id: str,
    spec_id: str,
    updates: Dict[str, Any]
) -> JSONResponse:
    """
    Update tool metadata before registration
    Allows editing name, description, category, etc.
    """
    if spec_id not in _specs_cache:
        raise HTTPException(status_code=404, detail="Spec not found")
    
    spec_data = _specs_cache[spec_id]
    
    # Find and update tool
    for tool in spec_data["tools"]:
        if tool["id"] == tool_id:
            # Update allowed fields
            allowed_updates = ["name", "display_name", "description", "category", "is_active"]
            for key, value in updates.items():
                if key in allowed_updates:
                    tool[key] = value
            
            return JSONResponse({
                "status": "success",
                "message": "Tool updated",
                "tool": tool
            })
    
    raise HTTPException(status_code=404, detail="Tool not found in spec")


@router.delete("/specs/{spec_id}")
async def delete_spec(spec_id: str) -> JSONResponse:
    """Delete uploaded spec and preview tools"""
    if spec_id not in _specs_cache:
        raise HTTPException(status_code=404, detail="Spec not found")
    
    del _specs_cache[spec_id]
    
    return JSONResponse({
        "status": "success",
        "message": "Spec deleted"
    })


@router.get("/specs/{spec_id}/download")
async def download_spec(spec_id: str):
    """Download original OpenAPI spec"""
    if spec_id not in _specs_cache:
        raise HTTPException(status_code=404, detail="Spec not found")
    
    spec_data = _specs_cache[spec_id]
    content = spec_data["content"]
    file_format = spec_data["format"]
    
    from fastapi.responses import Response
    
    media_type = "application/x-yaml" if file_format == "yaml" else "application/json"
    filename = spec_data.get("filename", f"spec.{file_format}")
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
