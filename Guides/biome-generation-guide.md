# 🌍 Biome Generation System Guide

Complete guide for generating large-scale biomes (3-5km) using the Unreal Engine MCP server's advanced biome generation system.

## 🎯 Overview

The biome generation system creates complete environments using Unreal Engine's:
- **Landscape Editor** for terrain generation
- **Procedural Foliage** for vegetation placement  
- **Material Painting** for surface textures
- **World Composition** for large-scale environments
- **Blueprint System** for custom environmental features

## 🌎 Available Biomes

### Primary Biomes (User Requested)
1. **Desert** - Dryland with dunes and oasis areas
2. **Plateau** - Large flat-topped mountain with low grass and rocks
3. **Dense Jungle** - Tree-dense jungle with bushes, rocks and caves
4. **Riverside** - Green lush river bed with lots of vegetation
5. **Tundra** - Large snowy land with rocks and frozen lakes
6. **Volcano** - Infernal scorched earth with burned trees and lava
7. **Marsh** - Rich wetland with knee-deep water and spaced trees
8. **Mushroom Kingdom** - Fantastical landscape filled with mushrooms

### Additional Biomes (AI Enhanced)
9. **Crystal Caverns** - Underground world of glowing crystal formations
10. **Floating Islands** - Mystical floating landmasses with energy bridges
11. **Bioluminescent Forest** - Magical forest with natural bioluminescence
12. **Mechanical Wasteland** - Post-apocalyptic landscape of rusted machinery
13. **Coral Reef** - Underwater paradise with vibrant coral formations

## 🔧 New MCP Tools

### Core Biome Generation
- `generate_biome_environment()` - Main biome generation tool
- `list_available_biomes()` - List all biome types with details
- `get_biome_details(biome_type)` - Get specific biome parameters
- `create_custom_landscape()` - Create base landscape without biome features

### Landscape Tools
- `create_landscape()` - Create base landscape actor
- `generate_heightmap()` - Apply procedural terrain
- `paint_landscape_material()` - Apply surface materials
- `create_landscape_layer()` - Add material layers

### Foliage Tools  
- `spawn_foliage()` - Place vegetation instances
- `create_foliage_type()` - Define custom foliage types
- `setup_procedural_foliage()` - Configure automatic spawning
- `paint_foliage()` - Manual foliage placement

## 🚀 Quick Start Examples

### Generate a Desert Biome
```python
# Create a 4km desert with oases
generate_biome_environment(
    biome_type="desert",
    location=[0, 0, 0],
    size=400000,  # 4km in centimeters
    name_prefix="SaharaDesert"
)
```

### Generate a Mystical Forest
```python
# Create a 5km bioluminescent forest
generate_biome_environment(
    biome_type="bioluminescent_forest",
    location=[10000, 0, 0],
    size=500000,  # 5km in centimeters
    name_prefix="EnchantedGlade"
)
```

### Generate Multiple Connected Biomes
```python
# Create a world with multiple biomes
biomes = [
    {"type": "desert", "location": [0, 0, 0]},
    {"type": "riverside", "location": [600000, 0, 0]},  # 6km east
    {"type": "dense_jungle", "location": [0, 600000, 0]},  # 6km north
    {"type": "volcano", "location": [600000, 600000, 0]}  # 6km northeast
]

for biome in biomes:
    generate_biome_environment(
        biome_type=biome["type"],
        location=biome["location"],
        size=400000,
        name_prefix=f"{biome['type']}_biome"
    )
```

## 📋 Biome Characteristics

### Desert Biome
- **Terrain**: Rolling dunes, occasional flat areas
- **Vegetation**: Sparse cacti, dead trees, desert grass (10% density)
- **Features**: Oases (1-3), sand dunes (5-15), rock formations (3-8)
- **Materials**: Sand (80%), rock (20%)

### Dense Jungle Biome  
- **Terrain**: Hilly with valleys and ridges
- **Vegetation**: Very dense trees, bushes, ferns (90% density)
- **Features**: Hidden caves (3-7), canopy bridges (2-4), clearings (1-3)
- **Materials**: Rich soil (70%), moss (20%), rock (10%)

### Floating Islands Biome
- **Terrain**: Separated floating landmasses
- **Vegetation**: Sky trees, wind grass, energy flowers (50% density)
- **Features**: Energy bridges (5-8), void portals (1-2), sky waterfalls (2-4)
- **Materials**: Floating stone (40%), energy crystal (30%), sky moss (20%)

### Coral Reef Biome
- **Terrain**: Underwater terrain with coral formations
- **Vegetation**: Brain coral, sea fans, kelp forests (80% density)
- **Features**: Coral mountains (2-4), underwater caves (3-6), sandy channels (2-5)
- **Materials**: Coral sand (40%), reef rock (30%), sea floor (20%)

## ⚙️ Advanced Configuration

### Custom Heightmap Settings
```python
custom_heightmap = {
    "frequency": 0.008,
    "amplitude": 1.2,
    "octaves": 6
}

generate_biome_environment(
    biome_type="plateau",
    custom_settings={"heightmap_override": custom_heightmap}
)
```

### Custom Foliage Density
```python
# Increase vegetation density by 50%
custom_foliage = {
    "foliage_density_multiplier": 1.5
}

generate_biome_environment(
    biome_type="dense_jungle",
    custom_settings=custom_foliage
)
```

### Material Overrides
```python
# Use custom materials
custom_materials = {
    "landscape_params": {
        "materials": [
            {"path": "/Game/Materials/CustomGrass", "layer_weight": 0.6, "name": "grass"},
            {"path": "/Game/Materials/CustomRock", "layer_weight": 0.4, "name": "rock"}
        ]
    }
}

generate_biome_environment(
    biome_type="plateau",
    custom_settings=custom_materials
)
```

## 📏 Size Guidelines

### Biome Sizes
- **Minimum**: 3km (300,000 cm)
- **Maximum**: 5km (500,000 cm)  
- **Default**: 4km (400,000 cm)
- **Recommended**: 4-4.5km for optimal performance

### Performance Considerations
- **3km biomes**: ~9 million sqm, best performance
- **4km biomes**: ~16 million sqm, balanced performance/size
- **5km biomes**: ~25 million sqm, requires powerful hardware

### Component Scaling
- Each landscape component ≈ 509m × 509m
- 3km biome ≈ 6×6 components (36 total)
- 4km biome ≈ 8×8 components (64 total)
- 5km biome ≈ 10×10 components (100 total)

## 🎨 Biome Features Breakdown

### Environmental Features by Type

**Water Features**: Oases, rivers, frozen lakes, hot springs, toxic pools
**Rock Features**: Formations, pillars, caves, cliffs, canyons  
**Vegetation Features**: Forest groves, mushroom circles, clearings
**Special Features**: Energy bridges, portals, ruins, machinery

### Feature Density by Biome
- **High Feature Density**: Crystal Caverns, Floating Islands, Mushroom Kingdom
- **Medium Feature Density**: Dense Jungle, Bioluminescent Forest, Coral Reef
- **Low Feature Density**: Desert, Tundra, Mechanical Wasteland

## 🔧 Technical Implementation

### Landscape Generation Pipeline
1. **Base Creation**: Create landscape actor with appropriate component count
2. **Heightmap Generation**: Apply noise-based terrain using biome parameters
3. **Material Painting**: Apply biome-specific surface materials
4. **Foliage Placement**: Spawn vegetation using procedural distribution
5. **Feature Addition**: Create special environmental features

### Noise Generation
- **Primary Noise**: Overall terrain shape (low frequency, high amplitude)
- **Detail Noise**: Surface variations (high frequency, low amplitude)  
- **Feature Noise**: Special formations (medium frequency, medium amplitude)

### Foliage Distribution Patterns
- **Uniform**: Even distribution across landscape
- **Clustered**: Grouped around specific areas
- **Water Gradient**: Density based on water proximity
- **Fungal Network**: Following underground networks
- **Mineral Veins**: Along geological formations

## 📊 Performance Optimization

### Biome Generation Times
- **3km biome**: ~30-60 seconds
- **4km biome**: ~60-120 seconds
- **5km biome**: ~120-300 seconds

*Times vary based on biome complexity and hardware*

### Memory Usage
- **Landscape**: ~50-200 MB per biome
- **Foliage**: ~100-500 MB per biome
- **Materials**: ~20-50 MB per biome
- **Total**: ~170-750 MB per biome

### Optimization Tips
1. Use smaller biome sizes for testing
2. Reduce foliage density for better performance
3. Use LOD (Level of Detail) systems for distant objects
4. Consider streaming for multiple biomes

## 🌟 Creative Use Cases

### Game Development
- **Open World Games**: Create diverse regions
- **Survival Games**: Varied biomes with unique resources
- **Adventure Games**: Themed areas with distinct challenges

### Film & Animation
- **Establishing Shots**: Large-scale environment reveals
- **Background Plates**: Detailed environmental backdrops
- **Concept Visualization**: Rapid prototyping of alien worlds

### Architectural Visualization
- **Urban Planning**: Landscape context for developments
- **Environmental Impact**: Visualize development in natural settings
- **Tourism**: Virtual environment exploration

### Education & Research  
- **Geography**: Visualize different ecosystem types
- **Climate Science**: Show environmental variations
- **Ecology**: Demonstrate habitat relationships

## 🚨 Troubleshooting

### Common Issues

**"Failed to connect to Unreal Engine"**
- Ensure Unreal Editor is running
- Check that UnrealMCP plugin is enabled
- Verify server port 55557 is available

**"Biome size must be between 3km and 5km"**
- Size parameter is in centimeters
- Use 300000-500000 for size parameter
- Example: 400000 = 4km

**"Unknown biome type"**
- Use exact biome names (case sensitive)
- Call `list_available_biomes()` for valid types
- Check spelling: "dense_jungle" not "jungle"

**"Landscape creation failed"**
- Ensure sufficient memory available
- Close other heavy applications
- Try smaller biome size

**"Foliage spawning failed"**
- Verify foliage assets exist in project
- Check landscape has proper materials applied
- Reduce foliage density if needed

### Performance Issues

**Slow generation times**
- Reduce biome size
- Lower foliage density multiplier
- Disable special features temporarily

**Memory errors**
- Close other applications
- Use 64-bit Unreal Engine
- Increase virtual memory

**Visual artifacts**
- Regenerate heightmap with different noise settings
- Adjust material blend settings
- Verify landscape component alignment

## 📚 Next Steps

1. **Experiment** with different biome types
2. **Combine** multiple biomes for large worlds  
3. **Customize** biome parameters for unique looks
4. **Integrate** with existing level design workflows
5. **Optimize** for your target platform performance

For more advanced techniques, see the [Tools Reference](tools-reference.md) and [Architectural Styles Guide](architectural-styles-guide.md).
