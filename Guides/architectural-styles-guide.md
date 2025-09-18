# 🏛️ Architectural Styles Guide

## Overview

The Unreal Engine MCP now supports rich architectural styles that can be applied to buildings, towns, and castles. These styles provide detailed descriptive text that enhances the visual and thematic appearance of your constructed worlds.

## 🎨 Available Architectural Styles

### Core Styles (User-Requested)

#### **Ruins**
- **Description**: Ancient structures showing the passage of time with weathered stone, crumbled walls, moss, and vegetation growth
- **Key Features**: Crumbled walls, collapsed sections, overgrown vegetation, weathered surfaces
- **Materials**: Weathered stone, moss, vegetation, cracked mortar
- **Use Cases**: Ancient civilizations, post-apocalyptic scenes, mysterious ruins

#### **Destroyed**
- **Description**: Partially destroyed structures with varying levels of damage from minor cracks to complete collapse
- **Key Features**: Collapsed roofs, missing walls, scattered debris, broken windows
- **Materials**: Broken concrete, twisted metal, shattered glass, debris
- **Use Cases**: War zones, disaster areas, abandoned cities

#### **Corrupted**
- **Description**: Malformed architecture with chaotic spiky protrusions and twisted geometry
- **Key Features**: Spiky protrusions, twisted spires, jagged edges, malformed geometry
- **Materials**: Dark metal, twisted stone, crystalline spikes, shadow matter
- **Use Cases**: Dark fantasy, horror themes, otherworldly environments

#### **Detailed**
- **Description**: Ornate architecture featuring intricate patterns, mosaics, and fractal designs
- **Key Features**: Fractal patterns, geometric mosaics, ornate carvings, detailed reliefs
- **Materials**: Carved stone, mosaic tiles, inlaid metals, decorated plaster
- **Use Cases**: Palaces, temples, high-culture buildings

#### **Elven**
- **Description**: Graceful organic architecture with flowing lines, curved roofs, and natural materials
- **Key Features**: Curved roofs, flowing lines, tall spires, organic shapes
- **Materials**: Living wood, crystal, silver accents, natural stone
- **Use Cases**: Fantasy forests, magical realms, nature-integrated buildings

#### **Orcish**
- **Description**: Brutal and intimidating architecture with heavy metal reinforcements and aggressive spikes
- **Key Features**: Iron spikes, heavy reinforcements, brutal angles, intimidating design
- **Materials**: Crude iron, rough timber, bone decorations, dark stone
- **Use Cases**: Fortress strongholds, barbaric settlements, military compounds

#### **Human**
- **Description**: Traditional medieval architecture emphasizing practicality with modest decorative elements
- **Key Features**: Practical design, timber framing, modest decoration, functional layout
- **Materials**: Timber framing, brick, thatch, clay tiles, rough stone
- **Use Cases**: Villages, towns, medieval settlements, practical buildings

### Extended Styles (AI-Enhanced)

#### **Crystalline**
- **Description**: Structures appearing carved from massive crystals with prismatic light effects
- **Key Features**: Faceted surfaces, light refraction, crystal spires, geometric forms
- **Materials**: Pure crystal, prismatic glass, light-conducting stone, ethereal metal
- **Use Cases**: Magical towers, sci-fi environments, alien structures

#### **Steampunk**
- **Description**: Industrial Victorian architecture enhanced with brass pipes and steam-powered mechanisms
- **Key Features**: Gear mechanisms, steam pipes, clockwork elements, industrial details
- **Materials**: Brass, copper pipes, wrought iron, tarnished metal, industrial glass
- **Use Cases**: Alternative history, retro-futuristic cities, industrial complexes

#### **Biomechanical**
- **Description**: Organic-mechanical hybrid architecture blending living tissue with mechanical systems
- **Key Features**: Organic curves, mechanical joints, pulsing surfaces, bio-integrated systems
- **Materials**: Living metal, organic composites, bio-luminescent elements, flexible membranes
- **Use Cases**: Alien environments, bio-tech facilities, futuristic settlements

#### **Celestial**
- **Description**: Divine architecture channeling heavenly elements with floating components and starlight patterns
- **Key Features**: Floating elements, divine light, star patterns, ethereal bridges
- **Materials**: White marble, gold inlay, starlight crystal, ethereal energy
- **Use Cases**: Temples, divine realms, heavenly citadels

#### **Volcanic**
- **Description**: Architecture forged from volcanic forces with obsidian walls and molten rock features
- **Key Features**: Lava channels, obsidian surfaces, volcanic vents, glowing fissures
- **Materials**: Obsidian, volcanic rock, molten metal, heat-resistant stone
- **Use Cases**: Volcanic regions, fire-themed environments, elemental strongholds

## 🛠️ Using Architectural Styles

### Available MCP Tools

#### `list_architectural_styles()`
Lists all available styles with complete descriptions and metadata.

```json
{
  "success": true,
  "styles": {...},
  "style_count": 12,
  "summary": "Available Architectural Styles:\n\n• Ruins: The structures are old and eroded..."
}
```

#### `get_architectural_style_info(style_name)`
Get detailed information about a specific style.

```json
{
  "success": true,
  "style": {
    "name": "Elven",
    "description": "The structures are of elven architecture...",
    "materials": ["living wood", "crystal", "silver accents"],
    "features": ["curved roofs", "flowing lines", "tall spires"],
    "colors": ["forest green", "silver", "natural wood"]
  }
}
```

#### `enhance_building_prompt(base_prompt, architectural_style, additional_details)`
Enhance a building prompt with style descriptions.

```json
{
  "success": true,
  "original_prompt": "Build a castle",
  "enhanced_prompt": "Build a castle\n\nArchitectural Style: Corrupted\n...",
  "style_used": "corrupted",
  "style_description": "The structures are spiky and malformed..."
}
```

### Enhanced Building Functions

All major building functions now support the `architectural_style` or `thematic_style` parameter:

#### Houses
```python
construct_house(
    width=1200,
    depth=1000,
    height=600,
    location=[0, 0, 0],
    name_prefix="MyHouse",
    house_style="modern",
    architectural_style="elven"  # NEW: Thematic style
)
```

#### Towns
```python
create_town(
    town_size="medium",
    building_density=0.7,
    location=[0, 0, 0],
    architectural_style="mixed",  # Legacy building types
    thematic_style="ruins"  # NEW: Overall thematic style
)
```

#### Castles
```python
create_castle_fortress(
    castle_size="large",
    location=[0, 0, 0],
    architectural_style="medieval",  # Legacy castle style
    thematic_style="corrupted"  # NEW: Thematic overlay
)
```

## 💡 Usage Examples

### Creating a Ruined Town
```python
# Create a town with ruins theme
create_town(
    town_size="medium",
    building_density=0.5,  # Lower density for ruins
    location=[0, 0, 0],
    name_prefix="AncientRuins",
    thematic_style="ruins"
)
```

### Building an Elven House
```python
# Create an elven-style house
construct_house(
    width=1000,
    depth=800,
    height=500,
    location=[0, 0, 0],
    name_prefix="ElvenDwelling",
    house_style="cottage",
    architectural_style="elven"
)
```

### Corrupted Castle Fortress
```python
# Create a dark, corrupted castle
create_castle_fortress(
    castle_size="large",
    location=[0, 0, 0],
    name_prefix="DarkFortress",
    architectural_style="gothic",
    thematic_style="corrupted"
)
```

### Enhanced Prompt Example
```python
# Enhance a building prompt with style
enhance_building_prompt(
    base_prompt="Create a mystical tower reaching toward the sky",
    architectural_style="crystalline",
    additional_details="Add rainbow light effects and floating crystal formations"
)
```

## 🎯 Best Practices

1. **Style Consistency**: Use the same thematic style across related buildings for cohesive environments
2. **Density Adjustment**: Lower building density for "ruins" and "destroyed" styles to show abandonment
3. **Size Scaling**: Larger structures work better with dramatic styles like "celestial" or "volcanic"
4. **Prompt Enhancement**: Use `enhance_building_prompt()` to generate rich descriptions for complex builds
5. **Combination Styles**: Mix legacy building styles with thematic styles for layered effects

## 🔧 Implementation Details

### Style Information Structure
```json
{
  "name": "Style Name",
  "description": "Detailed description of the architectural style",
  "materials": ["material1", "material2", "material3"],
  "features": ["feature1", "feature2", "feature3"],
  "colors": ["color1", "color2", "color3"]
}
```

### Return Value Enhancement
All building functions now return additional style information when a thematic style is applied:

```json
{
  "success": true,
  "actors": [...],
  "architectural_style": {
    "name": "Elven",
    "description": "The structures are of elven architecture...",
    "materials": [...],
    "features": [...],
    "colors": [...]
  },
  "style_description": "The structures are of elven architecture..."
}
```

## 🚀 Future Enhancements

- **Material Color Integration**: Automatic color application based on style palettes
- **Structural Modifications**: Physical alterations to match style descriptions
- **Style Mixing**: Combine multiple styles for unique hybrids
- **Dynamic Style Evolution**: Buildings that change styles over time
- **Custom Style Definitions**: User-defined architectural styles

---

*Use this guide to create rich, thematically consistent worlds with the enhanced Unreal Engine MCP architectural style system!*
