"""
Biome Definitions for Procedural Biome Generation

This module defines all available biomes with their characteristics including
landscape parameters, foliage settings, material assignments, and environmental features.
"""

import math
from typing import Dict, List, Tuple, Any

# Biome size constraints (in centimeters)
MIN_BIOME_SIZE = 300000  # 3km
MAX_BIOME_SIZE = 500000  # 5km

class BiomeDefinition:
    """Defines a complete biome with all its characteristics."""
    
    def __init__(self, name: str, description: str, landscape_params: Dict, 
                 foliage_config: Dict, environment_settings: Dict, 
                 special_features: List[Dict] = None):
        self.name = name
        self.description = description
        self.landscape_params = landscape_params
        self.foliage_config = foliage_config
        self.environment_settings = environment_settings
        self.special_features = special_features or []

# Core biome definitions
BIOME_DEFINITIONS = {
    "desert": BiomeDefinition(
        name="Desert",
        description="A dryland with dunes and oasis areas featuring sandy terrain and sparse vegetation",
        landscape_params={
            "heightmap_scale": {"x": 2.0, "y": 2.0, "z": 0.3},  # Low height variation
            "noise_settings": {
                "primary_noise": {"frequency": 0.005, "amplitude": 1.0, "octaves": 4},
                "dune_noise": {"frequency": 0.001, "amplitude": 0.8, "octaves": 2},
                "detail_noise": {"frequency": 0.02, "amplitude": 0.2, "octaves": 6}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.8, "name": "sand"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "rock"}
            ],
            "slope_settings": {"max_slope": 35.0, "erosion_strength": 0.3}
        },
        foliage_config={
            "density_multiplier": 0.1,  # Very sparse
            "species": [
                {"type": "cactus", "density": 0.05, "scale_range": (0.8, 1.5), "slope_max": 30},
                {"type": "dead_tree", "density": 0.02, "scale_range": (0.6, 1.2), "slope_max": 15},
                {"type": "desert_grass", "density": 0.03, "scale_range": (0.5, 1.0), "slope_max": 25}
            ],
            "distribution_pattern": "clustered"
        },
        environment_settings={
            "lighting": {"sun_intensity": 1.5, "sun_angle": 45, "sky_color": (0.9, 0.8, 0.6)},
            "weather": {"wind_strength": 0.3, "temperature": "hot", "humidity": 0.1},
            "atmosphere": {"fog_density": 0.1, "particle_effects": ["sand_particles"]}
        },
        special_features=[
            {"type": "oasis", "count": "1-3", "size": "small", "placement": "random_valleys"},
            {"type": "sand_dunes", "count": "5-15", "size": "large", "placement": "wind_pattern"},
            {"type": "rock_formations", "count": "3-8", "size": "medium", "placement": "ridge_lines"}
        ]
    ),
    
    "plateau": BiomeDefinition(
        name="Plateau", 
        description="A large, flat-topped mountain with low grass and scattered rocks",
        landscape_params={
            "heightmap_scale": {"x": 1.0, "y": 1.0, "z": 0.8},
            "noise_settings": {
                "primary_noise": {"frequency": 0.002, "amplitude": 1.0, "octaves": 3},
                "cliff_noise": {"frequency": 0.001, "amplitude": 0.9, "octaves": 2},
                "surface_noise": {"frequency": 0.01, "amplitude": 0.1, "octaves": 8}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.6, "name": "grass"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "rock"}
            ],
            "slope_settings": {"max_slope": 60.0, "erosion_strength": 0.5},
            "plateau_settings": {"flat_threshold": 0.1, "cliff_steepness": 0.9}
        },
        foliage_config={
            "density_multiplier": 0.4,
            "species": [
                {"type": "short_grass", "density": 0.3, "scale_range": (0.8, 1.2), "slope_max": 45},
                {"type": "rock_moss", "density": 0.1, "scale_range": (0.5, 0.8), "slope_max": 60},
                {"type": "highland_shrub", "density": 0.05, "scale_range": (0.7, 1.3), "slope_max": 30},
                {"type": "boulder", "density": 0.02, "scale_range": (1.0, 2.5), "slope_max": 20}
            ],
            "distribution_pattern": "uniform_sparse"
        },
        environment_settings={
            "lighting": {"sun_intensity": 1.2, "sun_angle": 60, "sky_color": (0.7, 0.8, 1.0)},
            "weather": {"wind_strength": 0.6, "temperature": "cool", "humidity": 0.4},
            "atmosphere": {"fog_density": 0.2, "particle_effects": ["wind_grass"]}
        },
        special_features=[
            {"type": "cliff_edges", "count": "continuous", "size": "large", "placement": "perimeter"},
            {"type": "stone_pillars", "count": "2-5", "size": "tall", "placement": "plateau_surface"},
            {"type": "ancient_ruins", "count": "0-2", "size": "medium", "placement": "plateau_center"}
        ]
    ),
    
    "dense_jungle": BiomeDefinition(
        name="Dense Jungle",
        description="A large tree dense jungle with few bushes, rocks and hidden caves",
        landscape_params={
            "heightmap_scale": {"x": 1.5, "y": 1.5, "z": 0.6},
            "noise_settings": {
                "primary_noise": {"frequency": 0.008, "amplitude": 1.0, "octaves": 5},
                "valley_noise": {"frequency": 0.003, "amplitude": 0.7, "octaves": 3},
                "detail_noise": {"frequency": 0.03, "amplitude": 0.3, "octaves": 7}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.7, "name": "rich_soil"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "moss"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "rock"}
            ],
            "slope_settings": {"max_slope": 45.0, "erosion_strength": 0.7}
        },
        foliage_config={
            "density_multiplier": 0.9,  # Very dense
            "species": [
                {"type": "large_tree", "density": 0.15, "scale_range": (1.5, 3.0), "slope_max": 35},
                {"type": "medium_tree", "density": 0.2, "scale_range": (1.0, 2.0), "slope_max": 40},
                {"type": "jungle_bush", "density": 0.4, "scale_range": (0.8, 1.5), "slope_max": 50},
                {"type": "fern", "density": 0.3, "scale_range": (0.5, 1.2), "slope_max": 45},
                {"type": "vine_clusters", "density": 0.1, "scale_range": (1.0, 2.0), "slope_max": 30}
            ],
            "distribution_pattern": "very_dense"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.8, "sun_angle": 50, "sky_color": (0.5, 0.8, 0.5)},
            "weather": {"wind_strength": 0.2, "temperature": "humid_hot", "humidity": 0.9},
            "atmosphere": {"fog_density": 0.4, "particle_effects": ["humidity_mist", "leaf_fall"]}
        },
        special_features=[
            {"type": "hidden_caves", "count": "3-7", "size": "medium", "placement": "hillsides"},
            {"type": "canopy_bridges", "count": "2-4", "size": "long", "placement": "tree_clusters"},
            {"type": "jungle_clearings", "count": "1-3", "size": "small", "placement": "valleys"}
        ]
    ),
    
    "riverside": BiomeDefinition(
        name="Riverside",
        description="A green lush river bed with lots of vegetation and flowing water",
        landscape_params={
            "heightmap_scale": {"x": 1.2, "y": 1.2, "z": 0.4},
            "noise_settings": {
                "primary_noise": {"frequency": 0.006, "amplitude": 1.0, "octaves": 4},
                "river_noise": {"frequency": 0.001, "amplitude": 0.8, "octaves": 2},
                "bank_noise": {"frequency": 0.015, "amplitude": 0.2, "octaves": 6}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.5, "name": "fertile_soil"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "grass"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "river_rock"}
            ],
            "slope_settings": {"max_slope": 30.0, "erosion_strength": 0.8},
            "water_settings": {"river_width": 500, "flow_speed": 1.0, "depth": 200}
        },
        foliage_config={
            "density_multiplier": 0.7,
            "species": [
                {"type": "willow_tree", "density": 0.08, "scale_range": (1.2, 2.5), "slope_max": 25, "water_proximity": 300},
                {"type": "reed_grass", "density": 0.4, "scale_range": (0.8, 1.5), "slope_max": 20, "water_proximity": 150},
                {"type": "flowering_bush", "density": 0.15, "scale_range": (0.7, 1.3), "slope_max": 35},
                {"type": "water_lily", "density": 0.1, "scale_range": (0.5, 1.0), "water_only": True},
                {"type": "cattail", "density": 0.2, "scale_range": (0.9, 1.4), "water_edge": True}
            ],
            "distribution_pattern": "water_gradient"
        },
        environment_settings={
            "lighting": {"sun_intensity": 1.1, "sun_angle": 55, "sky_color": (0.6, 0.8, 1.0)},
            "weather": {"wind_strength": 0.4, "temperature": "mild", "humidity": 0.7},
            "atmosphere": {"fog_density": 0.3, "particle_effects": ["water_mist", "pollen"]}
        },
        special_features=[
            {"type": "main_river", "count": "1", "size": "large", "placement": "center_flow"},
            {"type": "river_bends", "count": "3-6", "size": "natural", "placement": "along_river"},
            {"type": "small_islands", "count": "1-4", "size": "small", "placement": "river_wide_sections"},
            {"type": "wooden_bridges", "count": "1-2", "size": "medium", "placement": "crossing_points"}
        ]
    ),
    
    "tundra": BiomeDefinition(
        name="Tundra",
        description="A large snowy land with apparent rocks and frozen lakes",
        landscape_params={
            "heightmap_scale": {"x": 1.0, "y": 1.0, "z": 0.3},
            "noise_settings": {
                "primary_noise": {"frequency": 0.004, "amplitude": 1.0, "octaves": 3},
                "permafrost_noise": {"frequency": 0.002, "amplitude": 0.6, "octaves": 2},
                "surface_noise": {"frequency": 0.02, "amplitude": 0.1, "octaves": 8}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.6, "name": "snow"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.25, "name": "ice"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.15, "name": "exposed_rock"}
            ],
            "slope_settings": {"max_slope": 25.0, "erosion_strength": 0.2},
            "ice_settings": {"frozen_water_areas": 0.3, "ice_thickness": 100}
        },
        foliage_config={
            "density_multiplier": 0.2,
            "species": [
                {"type": "arctic_moss", "density": 0.1, "scale_range": (0.3, 0.8), "slope_max": 30},
                {"type": "low_shrub", "density": 0.05, "scale_range": (0.4, 0.9), "slope_max": 20},
                {"type": "ice_crystal", "density": 0.02, "scale_range": (0.8, 1.5), "slope_max": 15},
                {"type": "frozen_log", "density": 0.01, "scale_range": (1.0, 2.0), "slope_max": 10}
            ],
            "distribution_pattern": "scattered_sparse"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.9, "sun_angle": 30, "sky_color": (0.8, 0.9, 1.0)},
            "weather": {"wind_strength": 0.7, "temperature": "freezing", "humidity": 0.3},
            "atmosphere": {"fog_density": 0.2, "particle_effects": ["snow_particles", "ice_crystals"]}
        },
        special_features=[
            {"type": "frozen_lakes", "count": "2-5", "size": "medium", "placement": "low_areas"},
            {"type": "ice_formations", "count": "3-8", "size": "varied", "placement": "rock_outcrops"},
            {"type": "permafrost_mounds", "count": "5-12", "size": "small", "placement": "flat_areas"}
        ]
    ),
    
    "volcano": BiomeDefinition(
        name="Volcano",
        description="An infernal flame of scorched earth and rock with burned trees and lava flows",
        landscape_params={
            "heightmap_scale": {"x": 1.8, "y": 1.8, "z": 1.2},
            "noise_settings": {
                "primary_noise": {"frequency": 0.003, "amplitude": 1.0, "octaves": 4},
                "crater_noise": {"frequency": 0.001, "amplitude": 0.9, "octaves": 2},
                "lava_noise": {"frequency": 0.008, "amplitude": 0.4, "octaves": 5}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "volcanic_rock"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "lava_rock"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "ash"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "cooled_lava"}
            ],
            "slope_settings": {"max_slope": 70.0, "erosion_strength": 0.4},
            "volcanic_settings": {"crater_size": 1000, "lava_flow_paths": 3, "heat_zones": True}
        },
        foliage_config={
            "density_multiplier": 0.15,
            "species": [
                {"type": "charred_tree", "density": 0.03, "scale_range": (0.5, 1.5), "slope_max": 40},
                {"type": "volcanic_plant", "density": 0.05, "scale_range": (0.4, 1.0), "slope_max": 30},
                {"type": "heat_resistant_moss", "density": 0.08, "scale_range": (0.3, 0.7), "slope_max": 50},
                {"type": "obsidian_shard", "density": 0.02, "scale_range": (0.8, 1.8), "slope_max": 25}
            ],
            "distribution_pattern": "heat_gradient"
        },
        environment_settings={
            "lighting": {"sun_intensity": 1.3, "sun_angle": 70, "sky_color": (1.0, 0.6, 0.4)},
            "weather": {"wind_strength": 0.5, "temperature": "very_hot", "humidity": 0.2},
            "atmosphere": {"fog_density": 0.4, "particle_effects": ["ash_particles", "heat_shimmer", "ember_glow"]}
        },
        special_features=[
            {"type": "volcanic_crater", "count": "1", "size": "large", "placement": "peak"},
            {"type": "lava_flows", "count": "2-4", "size": "long", "placement": "downslope"},
            {"type": "hot_springs", "count": "1-3", "size": "small", "placement": "mid_elevation"},
            {"type": "volcanic_vents", "count": "3-8", "size": "small", "placement": "crater_rim"}
        ]
    ),
    
    "marsh": BiomeDefinition(
        name="Marsh",
        description="A rich field with knee-deep water that has tall trees spaced out with marshland vegetation",
        landscape_params={
            "heightmap_scale": {"x": 0.8, "y": 0.8, "z": 0.2},
            "noise_settings": {
                "primary_noise": {"frequency": 0.01, "amplitude": 1.0, "octaves": 4},
                "wetland_noise": {"frequency": 0.005, "amplitude": 0.6, "octaves": 3},
                "channel_noise": {"frequency": 0.02, "amplitude": 0.3, "octaves": 6}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "wetland_soil"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "marsh_grass"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "shallow_water"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "mud"}
            ],
            "slope_settings": {"max_slope": 15.0, "erosion_strength": 0.9},
            "water_settings": {"water_level": 50, "water_coverage": 0.6, "drainage_channels": True}
        },
        foliage_config={
            "density_multiplier": 0.6,
            "species": [
                {"type": "cypress_tree", "density": 0.08, "scale_range": (1.5, 3.0), "slope_max": 10, "water_tolerance": "high"},
                {"type": "marsh_grass", "density": 0.5, "scale_range": (0.8, 1.5), "slope_max": 20, "water_tolerance": "high"},
                {"type": "water_hyacinth", "density": 0.2, "scale_range": (0.5, 1.0), "water_only": True},
                {"type": "bog_moss", "density": 0.3, "scale_range": (0.4, 0.9), "slope_max": 15, "water_tolerance": "medium"},
                {"type": "mangrove_root", "density": 0.1, "scale_range": (1.0, 2.0), "water_edge": True}
            ],
            "distribution_pattern": "water_adapted"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.9, "sun_angle": 45, "sky_color": (0.7, 0.8, 0.8)},
            "weather": {"wind_strength": 0.3, "temperature": "warm_humid", "humidity": 0.8},
            "atmosphere": {"fog_density": 0.5, "particle_effects": ["marsh_mist", "fireflies", "pollen_drift"]}
        },
        special_features=[
            {"type": "drainage_channels", "count": "5-10", "size": "narrow", "placement": "natural_flow"},
            {"type": "raised_platforms", "count": "2-4", "size": "small", "placement": "dry_spots"},
            {"type": "fallen_logs", "count": "8-15", "size": "varied", "placement": "scattered"}
        ]
    ),
    
    "mushroom_kingdom": BiomeDefinition(
        name="Mushroom Kingdom",
        description="A place filled with mushrooms growing on rocks, plants and earth in a fantastical fungal landscape",
        landscape_params={
            "heightmap_scale": {"x": 1.3, "y": 1.3, "z": 0.5},
            "noise_settings": {
                "primary_noise": {"frequency": 0.007, "amplitude": 1.0, "octaves": 5},
                "mushroom_noise": {"frequency": 0.015, "amplitude": 0.4, "octaves": 7},
                "spore_noise": {"frequency": 0.03, "amplitude": 0.2, "octaves": 8}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "mycelium_soil"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "moss_covered_rock"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "fungal_growth"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "spore_dust"}
            ],
            "slope_settings": {"max_slope": 40.0, "erosion_strength": 0.6}
        },
        foliage_config={
            "density_multiplier": 0.8,
            "species": [
                {"type": "giant_mushroom", "density": 0.12, "scale_range": (2.0, 5.0), "slope_max": 30},
                {"type": "cluster_mushroom", "density": 0.25, "scale_range": (0.5, 1.5), "slope_max": 45},
                {"type": "glowing_mushroom", "density": 0.15, "scale_range": (0.8, 2.0), "slope_max": 35},
                {"type": "shelf_fungus", "density": 0.2, "scale_range": (0.4, 1.2), "slope_max": 60, "tree_attachment": True},
                {"type": "spore_pod", "density": 0.1, "scale_range": (0.6, 1.0), "slope_max": 25},
                {"type": "fungal_tree", "density": 0.05, "scale_range": (1.5, 3.0), "slope_max": 25}
            ],
            "distribution_pattern": "fungal_network"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.7, "sun_angle": 40, "sky_color": (0.6, 0.7, 0.9)},
            "weather": {"wind_strength": 0.2, "temperature": "cool_humid", "humidity": 0.9},
            "atmosphere": {"fog_density": 0.4, "particle_effects": ["spores", "bioluminescence", "fungal_glow"]}
        },
        special_features=[
            {"type": "mushroom_circles", "count": "8-15", "size": "varied", "placement": "mycelium_networks"},
            {"type": "giant_toadstools", "count": "3-6", "size": "massive", "placement": "clearings"},
            {"type": "underground_caves", "count": "2-4", "size": "medium", "placement": "hillsides"},
            {"type": "bioluminescent_pools", "count": "1-3", "size": "small", "placement": "valleys"}
        ]
    ),

    # 5 Additional Biome Definitions
    
    "crystal_caverns": BiomeDefinition(
        name="Crystal Caverns",
        description="An underground world of massive crystal formations with glowing minerals and underground lakes",
        landscape_params={
            "heightmap_scale": {"x": 2.0, "y": 2.0, "z": 0.7},
            "noise_settings": {
                "primary_noise": {"frequency": 0.004, "amplitude": 1.0, "octaves": 4},
                "crystal_noise": {"frequency": 0.012, "amplitude": 0.6, "octaves": 6},
                "cave_noise": {"frequency": 0.002, "amplitude": 0.8, "octaves": 3}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "crystal_rock"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "mineral_veins"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "cave_stone"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "glowing_crystal"}
            ],
            "slope_settings": {"max_slope": 80.0, "erosion_strength": 0.3},
            "cave_settings": {"ceiling_height": 2000, "underground_level": True, "crystal_density": 0.8}
        },
        foliage_config={
            "density_multiplier": 0.3,
            "species": [
                {"type": "crystal_formation", "density": 0.2, "scale_range": (1.0, 4.0), "slope_max": 70},
                {"type": "mineral_cluster", "density": 0.15, "scale_range": (0.5, 2.0), "slope_max": 80},
                {"type": "cave_moss", "density": 0.1, "scale_range": (0.3, 0.8), "slope_max": 45},
                {"type": "glowing_lichen", "density": 0.08, "scale_range": (0.4, 1.0), "slope_max": 60},
                {"type": "stalactite", "density": 0.05, "scale_range": (1.5, 3.5), "ceiling_only": True}
            ],
            "distribution_pattern": "mineral_veins"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.3, "sun_angle": 90, "sky_color": (0.4, 0.5, 0.8)},
            "weather": {"wind_strength": 0.1, "temperature": "cool", "humidity": 0.6},
            "atmosphere": {"fog_density": 0.2, "particle_effects": ["crystal_sparkle", "mineral_dust"]}
        },
        special_features=[
            {"type": "giant_geodes", "count": "2-4", "size": "massive", "placement": "cave_chambers"},
            {"type": "underground_river", "count": "1", "size": "long", "placement": "cave_floor"},
            {"type": "crystal_bridges", "count": "1-3", "size": "natural", "placement": "chasms"}
        ]
    ),
    
    "floating_islands": BiomeDefinition(
        name="Floating Islands",
        description="Mystical floating landmasses connected by energy bridges with antigravity vegetation",
        landscape_params={
            "heightmap_scale": {"x": 1.5, "y": 1.5, "z": 1.5},
            "noise_settings": {
                "primary_noise": {"frequency": 0.003, "amplitude": 1.0, "octaves": 3},
                "island_noise": {"frequency": 0.008, "amplitude": 0.7, "octaves": 5},
                "void_noise": {"frequency": 0.001, "amplitude": 0.9, "octaves": 2}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "floating_stone"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "energy_crystal"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "sky_moss"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "void_material"}
            ],
            "slope_settings": {"max_slope": 90.0, "erosion_strength": 0.1},
            "floating_settings": {"island_count": 8, "height_variation": 3000, "void_areas": 0.4}
        },
        foliage_config={
            "density_multiplier": 0.5,
            "species": [
                {"type": "sky_tree", "density": 0.08, "scale_range": (1.2, 2.5), "slope_max": 40, "floating": True},
                {"type": "wind_grass", "density": 0.3, "scale_range": (0.8, 1.5), "slope_max": 50, "floating": True},
                {"type": "energy_flower", "density": 0.12, "scale_range": (0.6, 1.2), "slope_max": 35},
                {"type": "gravity_vine", "density": 0.1, "scale_range": (2.0, 4.0), "hanging": True},
                {"type": "crystal_shard", "density": 0.05, "scale_range": (0.8, 2.0), "slope_max": 30}
            ],
            "distribution_pattern": "island_clusters"
        },
        environment_settings={
            "lighting": {"sun_intensity": 1.4, "sun_angle": 60, "sky_color": (0.7, 0.8, 1.0)},
            "weather": {"wind_strength": 0.8, "temperature": "mild", "humidity": 0.5},
            "atmosphere": {"fog_density": 0.6, "particle_effects": ["energy_wisps", "floating_dust", "aurora"]}
        },
        special_features=[
            {"type": "energy_bridges", "count": "5-8", "size": "connecting", "placement": "between_islands"},
            {"type": "void_portals", "count": "1-2", "size": "medium", "placement": "island_centers"},
            {"type": "sky_waterfalls", "count": "2-4", "size": "cascading", "placement": "island_edges"}
        ]
    ),
    
    "bioluminescent_forest": BiomeDefinition(
        name="Bioluminescent Forest",
        description="A magical forest where everything glows with natural bioluminescence in vibrant colors",
        landscape_params={
            "heightmap_scale": {"x": 1.4, "y": 1.4, "z": 0.6},
            "noise_settings": {
                "primary_noise": {"frequency": 0.006, "amplitude": 1.0, "octaves": 4},
                "glow_noise": {"frequency": 0.02, "amplitude": 0.3, "octaves": 8},
                "path_noise": {"frequency": 0.01, "amplitude": 0.5, "octaves": 5}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "glowing_soil"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "bio_moss"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "luminous_bark"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "energy_veins"}
            ],
            "slope_settings": {"max_slope": 45.0, "erosion_strength": 0.5}
        },
        foliage_config={
            "density_multiplier": 0.7,
            "species": [
                {"type": "glow_tree", "density": 0.15, "scale_range": (1.5, 3.0), "slope_max": 35, "bioluminescent": True},
                {"type": "light_moss", "density": 0.4, "scale_range": (0.3, 0.8), "slope_max": 60, "bioluminescent": True},
                {"type": "neon_flower", "density": 0.2, "scale_range": (0.5, 1.2), "slope_max": 40, "bioluminescent": True},
                {"type": "plasma_vine", "density": 0.1, "scale_range": (1.0, 2.5), "slope_max": 30, "tree_climbing": True},
                {"type": "fairy_light_pod", "density": 0.08, "scale_range": (0.6, 1.0), "slope_max": 25}
            ],
            "distribution_pattern": "bioluminescent_clusters"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.4, "sun_angle": 30, "sky_color": (0.2, 0.3, 0.6)},
            "weather": {"wind_strength": 0.3, "temperature": "mild_humid", "humidity": 0.8},
            "atmosphere": {"fog_density": 0.3, "particle_effects": ["bioluminescent_spores", "light_wisps", "color_shifts"]}
        },
        special_features=[
            {"type": "glow_paths", "count": "3-6", "size": "winding", "placement": "natural_trails"},
            {"type": "light_pools", "count": "2-4", "size": "small", "placement": "clearings"},
            {"type": "rainbow_groves", "count": "1-3", "size": "circular", "placement": "valleys"}
        ]
    ),
    
    "mechanical_wasteland": BiomeDefinition(
        name="Mechanical Wasteland",
        description="A post-apocalyptic landscape of rusted machinery, metal debris, and industrial remnants",
        landscape_params={
            "heightmap_scale": {"x": 1.6, "y": 1.6, "z": 0.8},
            "noise_settings": {
                "primary_noise": {"frequency": 0.005, "amplitude": 1.0, "octaves": 4},
                "debris_noise": {"frequency": 0.015, "amplitude": 0.4, "octaves": 7},
                "industrial_noise": {"frequency": 0.008, "amplitude": 0.6, "octaves": 5}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "rusted_metal"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "concrete_debris"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "oil_stains"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "toxic_waste"}
            ],
            "slope_settings": {"max_slope": 60.0, "erosion_strength": 0.4}
        },
        foliage_config={
            "density_multiplier": 0.25,
            "species": [
                {"type": "metal_scrap", "density": 0.2, "scale_range": (0.8, 3.0), "slope_max": 50},
                {"type": "rusted_pipe", "density": 0.15, "scale_range": (1.0, 4.0), "slope_max": 40},
                {"type": "industrial_gear", "density": 0.1, "scale_range": (0.5, 2.5), "slope_max": 45},
                {"type": "toxic_plant", "density": 0.05, "scale_range": (0.6, 1.5), "slope_max": 30},
                {"type": "broken_machinery", "density": 0.08, "scale_range": (1.5, 5.0), "slope_max": 25}
            ],
            "distribution_pattern": "industrial_clusters"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.8, "sun_angle": 50, "sky_color": (0.6, 0.5, 0.4)},
            "weather": {"wind_strength": 0.5, "temperature": "variable", "humidity": 0.3},
            "atmosphere": {"fog_density": 0.4, "particle_effects": ["rust_particles", "toxic_smoke", "sparks"]}
        },
        special_features=[
            {"type": "factory_ruins", "count": "2-4", "size": "large", "placement": "flat_areas"},
            {"type": "conveyor_systems", "count": "3-6", "size": "long", "placement": "connecting_ruins"},
            {"type": "toxic_pools", "count": "1-3", "size": "medium", "placement": "low_areas"},
            {"type": "scrap_piles", "count": "8-15", "size": "varied", "placement": "scattered"}
        ]
    ),
    
    "coral_reef": BiomeDefinition(
        name="Coral Reef",
        description="An underwater paradise with vibrant coral formations, sea plants, and marine structures",
        landscape_params={
            "heightmap_scale": {"x": 1.2, "y": 1.2, "z": 0.4},
            "noise_settings": {
                "primary_noise": {"frequency": 0.008, "amplitude": 1.0, "octaves": 5},
                "coral_noise": {"frequency": 0.02, "amplitude": 0.3, "octaves": 8},
                "current_noise": {"frequency": 0.004, "amplitude": 0.6, "octaves": 3}
            },
            "materials": [
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.4, "name": "coral_sand"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.3, "name": "reef_rock"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.2, "name": "sea_floor"},
                {"path": "/Engine/EngineMaterials/DefaultMaterial", "layer_weight": 0.1, "name": "deep_water"}
            ],
            "slope_settings": {"max_slope": 50.0, "erosion_strength": 0.6},
            "underwater_settings": {"water_depth": 1500, "visibility": 0.8, "current_strength": 0.4}
        },
        foliage_config={
            "density_multiplier": 0.8,
            "species": [
                {"type": "brain_coral", "density": 0.2, "scale_range": (1.0, 3.0), "slope_max": 40, "underwater": True},
                {"type": "sea_fan", "density": 0.15, "scale_range": (0.8, 2.0), "slope_max": 50, "underwater": True},
                {"type": "kelp_forest", "density": 0.25, "scale_range": (2.0, 5.0), "slope_max": 30, "underwater": True},
                {"type": "sea_anemone", "density": 0.1, "scale_range": (0.5, 1.5), "slope_max": 35, "underwater": True},
                {"type": "coral_tube", "density": 0.12, "scale_range": (0.6, 2.5), "slope_max": 45, "underwater": True},
                {"type": "sea_grass", "density": 0.3, "scale_range": (0.4, 1.2), "slope_max": 25, "underwater": True}
            ],
            "distribution_pattern": "reef_zones"
        },
        environment_settings={
            "lighting": {"sun_intensity": 0.6, "sun_angle": 80, "sky_color": (0.3, 0.6, 1.0)},
            "weather": {"wind_strength": 0.0, "temperature": "tropical", "humidity": 1.0},
            "atmosphere": {"fog_density": 0.1, "particle_effects": ["water_bubbles", "light_rays", "floating_particles"]}
        },
        special_features=[
            {"type": "coral_mountains", "count": "2-4", "size": "large", "placement": "reef_centers"},
            {"type": "underwater_caves", "count": "3-6", "size": "medium", "placement": "reef_edges"},
            {"type": "sandy_channels", "count": "2-5", "size": "winding", "placement": "between_reefs"},
            {"type": "kelp_forests", "count": "1-3", "size": "expansive", "placement": "deep_areas"}
        ]
    )
}

def get_biome_definition(biome_name: str) -> BiomeDefinition:
    """Get a biome definition by name."""
    return BIOME_DEFINITIONS.get(biome_name.lower().replace(" ", "_"))

def list_available_biomes() -> List[str]:
    """Get a list of all available biome names."""
    return list(BIOME_DEFINITIONS.keys())

def get_biome_size_range() -> Tuple[int, int]:
    """Get the valid size range for biomes in centimeters."""
    return (MIN_BIOME_SIZE, MAX_BIOME_SIZE)

def validate_biome_size(size: int) -> bool:
    """Validate if a biome size is within acceptable range."""
    return MIN_BIOME_SIZE <= size <= MAX_BIOME_SIZE

def get_biome_summary() -> Dict[str, Any]:
    """Get a summary of all available biomes."""
    summary = {
        "total_biomes": len(BIOME_DEFINITIONS),
        "size_range_km": {"min": MIN_BIOME_SIZE / 100000, "max": MAX_BIOME_SIZE / 100000},
        "biomes": {}
    }
    
    for name, definition in BIOME_DEFINITIONS.items():
        summary["biomes"][name] = {
            "name": definition.name,
            "description": definition.description,
            "features_count": len(definition.special_features),
            "foliage_species": len(definition.foliage_config["species"])
        }
    
    return summary
