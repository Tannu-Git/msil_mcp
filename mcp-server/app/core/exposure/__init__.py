"""
Exposure governance module - Tool visibility and access control

This module implements Layer B of the two-layer security model:
  Layer B (Exposure): Should user see this tool in tools/list?
  Layer A (Authorization): Can user execute this tool? (handled by policy engine)

Main export: exposure_manager singleton instance
"""

from .manager import ExposureManager, exposure_manager

__all__ = ["ExposureManager", "exposure_manager"]
