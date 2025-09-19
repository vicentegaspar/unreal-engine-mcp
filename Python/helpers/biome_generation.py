"""
Biome Generation Helper for Unreal Engine MCP Server

This module provides functions to generate complete biomes using Unreal Engine's
landscape, foliage, and material systems through the MCP interface.
"""

import logging
import math
import random
from typing import Dict, List, Any, Optional, Tuple
from .biome_definitions import (
    BIOME_DEFINITIONS, get_biome_definition, validate_biome_size,
    MIN_BIOME_SIZE, MAX_BIOME_SIZE
)

logger = logging.getLogger(__name__)

def generate_biome(unreal_connection, biome_type: str, location: List[float] = None, 
                  size: int = 400000, name_prefix: str = "BiomeGenerated",
                  custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate a complete biome with landscape, materials, and foliage.
    
    Args:
        unreal_connection: Connection to Unreal Engine
        biome_type: Type of biome to generate (e.g., "desert", "jungle")
        location: [X, Y, Z] position for biome center (default: [0, 0, 0])
        size: Size of biome in centimeters (3km to 5km)
        name_prefix: Prefix for generated assets
        custom_params: Override biome definition parameters
        
    Returns:
        Dict with generation results and statistics
    """
    if not unreal_connection:
        return {"success": False, "message": "No Unreal Engine connection"}
    
    if location is None:
        location = [0.0, 0.0, 0.0]
    
    # Validate biome size
    if not validate_biome_size(size):
        return {
            "success": False, 
            "message": f"Biome size must be between {MIN_BIOME_SIZE/100000}km and {MAX_BIOME_SIZE/100000}km"
        }
    
    # Get biome definition
    biome_def = get_biome_definition(biome_type)
    if not biome_def:
        return {"success": False, "message": f"Unknown biome type: {biome_type}"}
    
    logger.info(f"Generating {biome_def.name} biome at {location} with size {size/100000}km")
    
    try:
        # Phase 1: Create landscape
        landscape_result = create_biome_landscape(
            unreal_connection, biome_def, location, size, name_prefix, custom_params
        )
        if not landscape_result.get("success", False):
            return landscape_result
        
        landscape_name = landscape_result.get("landscape_name")
        
        # Phase 2: Generate heightmap with biome-specific terrain
        heightmap_result = generate_biome_heightmap(
            unreal_connection, biome_def, landscape_name, custom_params
        )
        if not heightmap_result.get("success", False):
            return heightmap_result
        
        # Phase 3: Apply materials and textures
        material_result = apply_biome_materials(
            unreal_connection, biome_def, landscape_name, custom_params
        )
        if not material_result.get("success", False):
            logger.warning(f"Material application failed: {material_result.get('message')}")
        
        # Phase 4: Generate foliage
        foliage_result = generate_biome_foliage(
            unreal_connection, biome_def, landscape_name, location, size, custom_params
        )
        if not foliage_result.get("success", False):
            logger.warning(f"Foliage generation failed: {foliage_result.get('message')}")
        
        # Phase 5: Add special features
        features_result = add_biome_special_features(
            unreal_connection, biome_def, landscape_name, location, size, custom_params
        )
        if not features_result.get("success", False):
            logger.warning(f"Special features failed: {features_result.get('message')}")
        
        # Compile final results
        total_assets = (
            1 +  # landscape
            len(material_result.get("materials_applied", [])) +
            foliage_result.get("foliage_instances", 0) +
            len(features_result.get("special_features", []))
        )
        
        return {
            "success": True,
            "biome_type": biome_type,
            "biome_name": biome_def.name,
            "landscape_name": landscape_name,
            "location": location,
            "size_km": size / 100000,
            "assets_created": total_assets,
            "phases": {
                "landscape": landscape_result,
                "heightmap": heightmap_result,
                "materials": material_result,
                "foliage": foliage_result,
                "features": features_result
            },
            "message": f"{biome_def.name} biome generated successfully with {total_assets} assets"
        }
        
    except Exception as e:
        logger.error(f"Biome generation failed: {e}")
        return {"success": False, "message": f"Biome generation error: {str(e)}"}

def create_biome_landscape(unreal_connection, biome_def, location: List[float], 
                          size: int, name_prefix: str, custom_params: Dict = None) -> Dict[str, Any]:
    """Create the base landscape for the biome."""
    
    # Calculate landscape dimensions based on biome size
    # Each landscape component is roughly 509m x 509m (63 quads * 100cm * 8.1 scale)
    component_size_cm = 50900
    component_count = max(4, min(32, math.ceil(size / component_size_cm)))
    
    # Ensure even number for symmetry
    if component_count % 2 != 0:
        component_count += 1
    
    landscape_params = {
        "location": location,
        "component_count_x": component_count,
        "component_count_y": component_count,
        "quads_per_component": 63,
        "subsection_size_quads": 31
    }
    
    # Override with custom parameters if provided
    if custom_params and "landscape_params" in custom_params:
        landscape_params.update(custom_params["landscape_params"])
    
    try:
        response = unreal_connection.send_command("create_landscape", landscape_params)
        
        if response and response.get("status") == "success":
            return {
                "success": True,
                "landscape_name": response.get("landscape_name"),
                "size_x": response.get("size_x"),
                "size_y": response.get("size_y"),
                "component_count": component_count,
                "message": "Landscape created successfully"
            }
        else:
            error_msg = response.get("error", "Unknown landscape creation error") if response else "No response"
            return {"success": False, "message": f"Failed to create landscape: {error_msg}"}
            
    except Exception as e:
        return {"success": False, "message": f"Landscape creation error: {str(e)}"}

def generate_biome_heightmap(unreal_connection, biome_def, landscape_name: str, 
                           custom_params: Dict = None) -> Dict[str, Any]:
    """Generate biome-specific heightmap terrain."""
    
    # Get heightmap parameters from biome definition
    landscape_params = biome_def.landscape_params
    noise_settings = landscape_params.get("noise_settings", {})
    
    # Override with custom parameters
    if custom_params and "heightmap_override" in custom_params:
        noise_settings.update(custom_params["heightmap_override"])
    
    heightmap_params = {
        "landscape_name": landscape_name,
        "noise_settings": noise_settings
    }
    
    try:
        response = unreal_connection.send_command("generate_heightmap", heightmap_params)
        
        if response and response.get("status") == "success":
            return {
                "success": True,
                "heightmap_size_x": response.get("heightmap_size_x"),
                "heightmap_size_y": response.get("heightmap_size_y"),
                "noise_layers_applied": len(noise_settings),
                "message": "Heightmap generated successfully"
            }
        else:
            error_msg = response.get("error", "Unknown heightmap error") if response else "No response"
            return {"success": False, "message": f"Failed to generate heightmap: {error_msg}"}
            
    except Exception as e:
        return {"success": False, "message": f"Heightmap generation error: {str(e)}"}

def apply_biome_materials(unreal_connection, biome_def, landscape_name: str, 
                         custom_params: Dict = None) -> Dict[str, Any]:
    """Apply biome-specific materials and textures to the landscape."""
    
    materials = biome_def.landscape_params.get("materials", [])
    if not materials:
        return {"success": True, "materials_applied": [], "message": "No materials to apply"}
    
    applied_materials = []
    
    for material_config in materials:
        material_params = {
            "landscape_name": landscape_name,
            "material_path": material_config.get("path"),
            "layer_name": material_config.get("name"),
            "layer_weight": material_config.get("layer_weight", 1.0)
        }
        
        try:
            response = unreal_connection.send_command("paint_landscape_material", material_params)
            
            if response and response.get("status") == "success":
                applied_materials.append({
                    "name": material_config.get("name"),
                    "path": material_config.get("path"),
                    "weight": material_config.get("layer_weight")
                })
            else:
                logger.warning(f"Failed to apply material {material_config.get('name')}: {response}")
                
        except Exception as e:
            logger.warning(f"Material application error for {material_config.get('name')}: {e}")
    
    return {
        "success": True,
        "materials_applied": applied_materials,
        "materials_count": len(applied_materials),
        "message": f"Applied {len(applied_materials)} materials to landscape"
    }

def generate_biome_foliage(unreal_connection, biome_def, landscape_name: str, 
                          location: List[float], size: int, custom_params: Dict = None) -> Dict[str, Any]:
    """Generate procedural foliage for the biome."""
    
    foliage_config = biome_def.foliage_config
    species = foliage_config.get("species", [])
    
    if not species:
        return {"success": True, "foliage_instances": 0, "message": "No foliage species defined"}
    
    density_multiplier = foliage_config.get("density_multiplier", 1.0)
    total_area_sqm = (size / 100) ** 2  # Convert cm to meters, then square
    
    foliage_instances = 0
    spawned_species = []
    
    for species_config in species:
        species_density = species_config.get("density", 0.1)
        effective_density = species_density * density_multiplier
        
        # Calculate number of instances based on area and density
        instance_count = int(total_area_sqm * effective_density)
        
        if instance_count > 0:
            foliage_params = {
                "landscape_name": landscape_name,
                "species_type": species_config.get("type"),
                "instance_count": instance_count,
                "scale_range": species_config.get("scale_range", [1.0, 1.0]),
                "max_slope": species_config.get("slope_max", 45),
                "distribution_pattern": foliage_config.get("distribution_pattern", "uniform")
            }
            
            # Add special placement rules
            if "water_proximity" in species_config:
                foliage_params["water_proximity"] = species_config["water_proximity"]
            if "water_only" in species_config:
                foliage_params["water_only"] = species_config["water_only"]
            if "water_edge" in species_config:
                foliage_params["water_edge"] = species_config["water_edge"]
            
            try:
                response = unreal_connection.send_command("spawn_foliage", foliage_params)
                
                if response and response.get("status") == "success":
                    instances_spawned = response.get("instances_spawned", instance_count)
                    foliage_instances += instances_spawned
                    spawned_species.append({
                        "type": species_config.get("type"),
                        "instances": instances_spawned,
                        "density": effective_density
                    })
                else:
                    logger.warning(f"Failed to spawn foliage {species_config.get('type')}: {response}")
                    
            except Exception as e:
                logger.warning(f"Foliage spawning error for {species_config.get('type')}: {e}")
    
    return {
        "success": True,
        "foliage_instances": foliage_instances,
        "species_spawned": spawned_species,
        "species_count": len(spawned_species),
        "message": f"Spawned {foliage_instances} foliage instances of {len(spawned_species)} species"
    }

def add_biome_special_features(unreal_connection, biome_def, landscape_name: str, 
                              location: List[float], size: int, custom_params: Dict = None) -> Dict[str, Any]:
    """Add biome-specific special features like oases, caves, etc."""
    
    special_features = biome_def.special_features
    if not special_features:
        return {"success": True, "special_features": [], "message": "No special features defined"}
    
    created_features = []
    
    for feature_config in special_features:
        feature_type = feature_config.get("type")
        feature_count = parse_count_range(feature_config.get("count", "1"))
        feature_size = feature_config.get("size", "medium")
        placement = feature_config.get("placement", "random")
        
        for i in range(feature_count):
            feature_location = calculate_feature_location(location, size, placement, i, feature_count)
            
            feature_params = {
                "feature_type": feature_type,
                "location": feature_location,
                "size": feature_size,
                "landscape_name": landscape_name,
                "biome_context": biome_def.name.lower()
            }
            
            try:
                # Use existing tools to create features based on type
                feature_result = create_special_feature(unreal_connection, feature_params)
                
                if feature_result.get("success", False):
                    created_features.append({
                        "type": feature_type,
                        "location": feature_location,
                        "size": feature_size,
                        "actors": feature_result.get("actors", [])
                    })
                else:
                    logger.warning(f"Failed to create feature {feature_type}: {feature_result}")
                    
            except Exception as e:
                logger.warning(f"Special feature creation error for {feature_type}: {e}")
    
    return {
        "success": True,
        "special_features": created_features,
        "features_count": len(created_features),
        "message": f"Created {len(created_features)} special features"
    }

def create_special_feature(unreal_connection, feature_params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a specific special feature using existing MCP tools."""
    
    feature_type = feature_params.get("feature_type")
    location = feature_params.get("location")
    size = feature_params.get("size", "medium")
    
    # Map feature types to existing MCP commands
    if feature_type in ["oasis", "jungle_clearings"]:
        # Create a small area with different vegetation
        return create_clearing_feature(unreal_connection, feature_params)
        
    elif feature_type in ["sand_dunes", "rock_formations", "stone_pillars"]:
        # Create rock/stone formations
        return create_rock_formation_feature(unreal_connection, feature_params)
        
    elif feature_type in ["hidden_caves", "underground_caves"]:
        # Create cave entrances
        return create_cave_feature(unreal_connection, feature_params)
        
    elif feature_type in ["frozen_lakes", "hot_springs", "bioluminescent_pools"]:
        # Create water features
        return create_water_feature(unreal_connection, feature_params)
        
    elif feature_type in ["volcanic_crater", "volcanic_vents"]:
        # Create volcanic features
        return create_volcanic_feature(unreal_connection, feature_params)
        
    elif feature_type in ["mushroom_circles", "giant_toadstools"]:
        # Create mushroom formations
        return create_mushroom_feature(unreal_connection, feature_params)
        
    else:
        # Generic feature creation
        return create_generic_feature(unreal_connection, feature_params)

def create_clearing_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create a clearing with modified vegetation."""
    location = params.get("location")
    size_map = {"small": 500, "medium": 1000, "large": 2000}
    clearing_size = size_map.get(params.get("size"), 1000)
    
    # Create a circular area with less dense foliage
    actors = []
    
    # Add some decorative elements
    for i in range(3, 8):
        offset_x = random.uniform(-clearing_size/2, clearing_size/2)
        offset_y = random.uniform(-clearing_size/2, clearing_size/2)
        
        actor_location = [
            location[0] + offset_x,
            location[1] + offset_y,
            location[2]
        ]
        
        # Create decorative rocks or logs
        actor_name = f"ClearingDecor_{params.get('feature_type')}_{i}"
        mesh_path = "/Engine/BasicShapes/Cube.Cube"  # Placeholder
        
        try:
            from .actor_utilities import spawn_blueprint_actor
            result = spawn_blueprint_actor(unreal_connection, "BasicActor_BP", actor_name, actor_location)
            if result.get("success"):
                actors.append(result)
        except:
            pass
    
    return {
        "success": True,
        "actors": actors,
        "feature_type": params.get("feature_type"),
        "message": f"Created clearing feature with {len(actors)} decorative elements"
    }

def create_rock_formation_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create rock formations using existing tower/wall tools."""
    location = params.get("location")
    
    try:
        # Use existing create_tower function with rocky style
        response = unreal_connection.send_command("create_tower", {
            "height": random.randint(3, 8),
            "base_size": random.randint(2, 5),
            "block_size": random.uniform(150, 300),
            "location": location,
            "name_prefix": f"RockFormation_{params.get('feature_type')}",
            "mesh": "/Engine/BasicShapes/Cube.Cube",
            "tower_style": "square"
        })
        
        if response and response.get("success"):
            return {
                "success": True,
                "actors": response.get("actors", []),
                "feature_type": params.get("feature_type"),
                "message": "Rock formation created successfully"
            }
        else:
            return {"success": False, "message": "Failed to create rock formation"}
            
    except Exception as e:
        return {"success": False, "message": f"Rock formation error: {str(e)}"}

def create_cave_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create cave entrance markers."""
    location = params.get("location")
    
    try:
        # Create cave entrance using arch tool
        response = unreal_connection.send_command("create_arch", {
            "radius": random.uniform(200, 500),
            "segments": random.randint(5, 8),
            "location": location,
            "name_prefix": f"CaveEntrance_{params.get('feature_type')}",
            "mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        
        if response and response.get("success"):
            return {
                "success": True,
                "actors": response.get("actors", []),
                "feature_type": params.get("feature_type"),
                "message": "Cave entrance created successfully"
            }
        else:
            return {"success": False, "message": "Failed to create cave entrance"}
            
    except Exception as e:
        return {"success": False, "message": f"Cave creation error: {str(e)}"}

def create_water_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create water features like lakes or pools."""
    location = params.get("location")
    
    # Create a simple water body using scaled cubes
    actors = []
    pool_radius = random.uniform(300, 800)
    
    for i in range(8, 15):
        angle = (2 * math.pi * i) / 15
        x = location[0] + pool_radius * math.cos(angle)
        y = location[1] + pool_radius * math.sin(angle)
        z = location[2] - 50  # Slightly below ground
        
        actor_name = f"WaterFeature_{params.get('feature_type')}_{i}"
        
        try:
            response = unreal_connection.send_command("spawn_actor", {
                "name": actor_name,
                "type": "StaticMeshActor",
                "location": [x, y, z],
                "scale": [pool_radius/100, pool_radius/100, 0.5],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            
            if response and response.get("success"):
                actors.append(response)
                
        except Exception as e:
            logger.warning(f"Water feature element creation failed: {e}")
    
    return {
        "success": True,
        "actors": actors,
        "feature_type": params.get("feature_type"),
        "message": f"Water feature created with {len(actors)} elements"
    }

def create_volcanic_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create volcanic features like craters or vents."""
    return create_rock_formation_feature(unreal_connection, params)

def create_mushroom_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create mushroom formations."""
    return create_rock_formation_feature(unreal_connection, params)

def create_generic_feature(unreal_connection, params: Dict) -> Dict[str, Any]:
    """Create a generic feature using basic shapes."""
    return create_rock_formation_feature(unreal_connection, params)

# Utility functions
def parse_count_range(count_str: str) -> int:
    """Parse count ranges like '1-3' or '5-10'."""
    if isinstance(count_str, int):
        return count_str
    
    if isinstance(count_str, str):
        if "-" in count_str:
            try:
                min_val, max_val = map(int, count_str.split("-"))
                return random.randint(min_val, max_val)
            except ValueError:
                return 1
        else:
            try:
                return int(count_str)
            except ValueError:
                return 1
    
    return 1

def calculate_feature_location(base_location: List[float], biome_size: int, 
                             placement: str, index: int, total_count: int) -> List[float]:
    """Calculate location for a special feature based on placement strategy."""
    
    if placement == "random":
        # Random placement within biome bounds
        half_size = biome_size / 2
        return [
            base_location[0] + random.uniform(-half_size, half_size),
            base_location[1] + random.uniform(-half_size, half_size),
            base_location[2]
        ]
    
    elif placement == "perimeter":
        # Place around the biome perimeter
        angle = (2 * math.pi * index) / total_count
        radius = biome_size * 0.4
        return [
            base_location[0] + radius * math.cos(angle),
            base_location[1] + radius * math.sin(angle),
            base_location[2]
        ]
    
    elif placement == "center":
        # Place near the center
        offset = random.uniform(-biome_size * 0.1, biome_size * 0.1)
        return [
            base_location[0] + offset,
            base_location[1] + offset,
            base_location[2]
        ]
    
    else:
        # Default to random placement
        return calculate_feature_location(base_location, biome_size, "random", index, total_count)
