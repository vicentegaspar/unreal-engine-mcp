# Unreal MCP Advanced Server

A streamlined version of the Unreal MCP server that focuses on advanced composition, building tools, and large-scale biome generation, featuring **33 tools** including 4 new biome generation tools.

## What's Included

This server contains only the essential tools needed for advanced level building and composition:

### Essential Actor Management (5 tools)
- `get_actors_in_level()` - List all actors
- `find_actors_by_name(pattern)` - Find actors by pattern
- `spawn_actor(name, type, location, rotation)` - Create basic actors
- `delete_actor(name)` - Remove actors
- `set_actor_transform(name, location, rotation, scale)` - Modify transforms

### Essential Blueprint Tools (6 tools)
*Minimal set needed for physics actors*
- `create_blueprint(name, parent_class)` - Create Blueprint classes
- `add_component_to_blueprint()` - Add components to Blueprints
- `set_static_mesh_properties()` - Set mesh properties
- `set_physics_properties()` - Configure physics
- `compile_blueprint(name)` - Compile Blueprint changes
- `spawn_blueprint_actor()` - Spawn from Blueprint

### Advanced Composition Tools (10 tools)
*The main focus - advanced building and composition tools from the merge request*
- `create_pyramid(base_size, block_size, location, ...)` - Build pyramids
- `create_wall(length, height, block_size, location, orientation, ...)` - Generate walls
- `create_tower(levels, block_size, location, ...)` - Stack towers
- `create_staircase(steps, step_size, location, ...)` - Build staircases
- `construct_house(width, depth, height, location, ...)` - **Enhanced** game-ready houses
- `create_arch(radius, segments, location, ...)` - Arch structures
- `spawn_physics_blueprint_actor (name, mesh_path, location, mass, ...)` - Physics objects
- `create_maze(rows, cols, cell_size, wall_height, location)` - Grid mazes
- `create_obstacle_course(checkpoints, spacing, location)` - Obstacle courses

### Large-Scale Biome Generation (4 tools)
*NEW - Complete 3-5km biome environments with landscapes, foliage, and features*
- `generate_biome_environment(biome_type, location, size, ...)` - **Main biome generator**
- `list_available_biomes()` - List all 13 biome types with descriptions
- `get_biome_details(biome_type)` - Get detailed biome parameters
- `create_custom_landscape(location, size_km, ...)` - Create base landscape terrain

## Enhanced House Construction

The `construct_house` function has been significantly improved:

### Key Improvements:
- **Faster Spawning**: Uses large wall segments instead of individual blocks (20-30 actors vs 300+)
- **Realistic Proportions**: Default 12m x 10m x 6m house with proper room sizes
- **Smooth Walls**: Thin 20cm walls using scaled actors for clean appearance
- **Architectural Features**: 
  - Proper foundation and floor
  - Door opening (1.2m x 2.4m)
  - Window cutouts with proper placement
  - Pitched roof with realistic angle and overhang
  - Style-specific details (chimney, porch, garage)

### House Styles:
- **Modern**: Clean lines, garage door, flat details
- **Cottage**: Smaller size (80%), chimney, cozy proportions  
- **Mansion**: Larger size (150%), front porch with columns, chimney

### Example Usage:
```python
# Create a modern house
construct_house(house_style="modern")

# Create a cottage at specific location
construct_house(location=[1000, 0, 0], house_style="cottage")

# Create a large mansion
construct_house(width=1500, depth=1200, house_style="mansion")
```

## Large-Scale Biome Generation

The new biome generation system creates complete 3-5km environments using Unreal Engine's landscape editor, procedural foliage, and world composition systems.

### Available Biomes (13 types):

**Primary Biomes:**
- **Desert**: Dryland with dunes and oasis areas
- **Plateau**: Large flat-topped mountain with low grass and rocks
- **Dense Jungle**: Tree-dense jungle with bushes, rocks and caves
- **Riverside**: Green lush river bed with lots of vegetation
- **Tundra**: Large snowy land with rocks and frozen lakes
- **Volcano**: Infernal scorched earth with burned trees and lava
- **Marsh**: Rich wetland with knee-deep water and spaced trees
- **Mushroom Kingdom**: Fantastical landscape filled with mushrooms

**Advanced Biomes:**
- **Crystal Caverns**: Underground world of glowing crystal formations
- **Floating Islands**: Mystical floating landmasses with energy bridges
- **Bioluminescent Forest**: Magical forest with natural bioluminescence
- **Mechanical Wasteland**: Post-apocalyptic landscape of rusted machinery
- **Coral Reef**: Underwater paradise with vibrant coral formations

### Key Features:
- **Procedural Terrain**: Noise-based heightmap generation
- **Material Painting**: Biome-appropriate surface textures
- **Vegetation Systems**: Procedural foliage placement with density controls
- **Special Features**: Unique environmental elements (caves, oases, formations)
- **Performance Optimized**: Efficient generation for large-scale environments

### Example Usage:
```python
# Generate a 4km desert biome
generate_biome_environment(
    biome_type="desert",
    location=[0, 0, 0], 
    size=400000,  # 4km in centimeters
    name_prefix="SaharaDesert"
)

# Create a mystical floating islands biome
generate_biome_environment(
    biome_type="floating_islands",
    location=[600000, 0, 0],  # 6km away
    size=500000,  # 5km maximum size
    name_prefix="SkyRealm"
)

# List all available biome types
list_available_biomes()

# Get detailed parameters for a specific biome
get_biome_details("bioluminescent_forest")
```

## What's Removed

The following tool categories were removed to reduce complexity:
- UMG/Widget tools (5+ tools)
- Advanced Blueprint node management (8+ tools)
- Detailed physics material properties (3+ tools)
- Project configuration tools (2+ tools)
- Editor viewport/screenshot tools (3+ tools)
- Advanced component property setters (2+ tools)

## Usage

Run the streamlined server instead of the full one:

```bash
python unreal_mcp_server_advanced.py
```

## Benefits

- **Comprehensive**: 33 tools including advanced biome generation
- **Large-Scale**: Create 3-5km biome environments with complete ecosystems
- **Focused**: Concentrates on advanced building/composition + procedural worlds
- **Performance Optimized**: Efficient generation for massive landscapes
- **Self-contained**: No external tool dependencies
- **Unreal Integration**: Uses native Landscape Editor, Foliage, and World Composition

This server is perfect for users who want to create large-scale worlds, complete biome systems, advanced building compositions, and complex structures with both manual placement and procedural generation capabilities. 