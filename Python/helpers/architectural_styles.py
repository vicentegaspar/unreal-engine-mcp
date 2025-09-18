"""
Architectural Styles Helper Module for Unreal MCP Server.

Contains definitions and descriptions for various architectural styles that can be applied
to buildings and structures. These styles provide detailed descriptive text that can be
used in prompts to guide building creation with specific aesthetic characteristics.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Complete architectural style definitions with detailed descriptions
ARCHITECTURAL_STYLES = {
    # User-requested styles
    "ruins": {
        "name": "Ruins",
        "description": "The structures are old and eroded with crumbled parts and moss and vegetation. Ancient stone walls show signs of weathering, with gaps where blocks have fallen. Ivy and vines crawl up deteriorated surfaces, while patches of moss cover the dampest areas. Some sections have completely collapsed, leaving only foundations or partial walls standing.",
        "materials": ["weathered stone", "moss", "vegetation", "cracked mortar"],
        "features": ["crumbled walls", "collapsed sections", "overgrown vegetation", "weathered surfaces"],
        "colors": ["earth tones", "green moss", "grey stone", "brown vegetation"]
    },
    
    "destroyed": {
        "name": "Destroyed", 
        "description": "The structures are partially destroyed in different levels. Some buildings show minor damage with broken windows and cracked walls, while others are severely damaged with entire sections missing. Debris scattered around the area tells the story of destruction, with twisted metal, broken concrete, and collapsed roofs creating a post-apocalyptic atmosphere.",
        "materials": ["broken concrete", "twisted metal", "shattered glass", "debris"],
        "features": ["collapsed roofs", "missing walls", "scattered debris", "broken windows"],
        "colors": ["grey concrete", "rust red", "charcoal black", "dust brown"]
    },
    
    "corrupted": {
        "name": "Corrupted",
        "description": "The structures are spiky and malformed. All parts of the structures display chaotic spiky protrusions that mold the form. Angular, jagged edges emerge unnaturally from walls and roofs, creating an otherworldly and menacing appearance. The architecture seems infected by some dark force, with twisted spires and irregular growths distorting the original design.",
        "materials": ["dark metal", "twisted stone", "crystalline spikes", "shadow matter"],
        "features": ["spiky protrusions", "twisted spires", "jagged edges", "malformed geometry"],
        "colors": ["dark purple", "corrupted red", "shadow black", "sickly green"]
    },
    
    "detailed": {
        "name": "Detailed",
        "description": "The structure is decorated with intricate repeating patterns. Mosaics and fractals are present here. Every surface displays elaborate geometric designs, with tessellating patterns that create visual complexity. Ornate carvings cover walls, doorways, and architectural elements, showcasing masterful craftsmanship and attention to detail.",
        "materials": ["carved stone", "mosaic tiles", "inlaid metals", "decorated plaster"],
        "features": ["fractal patterns", "geometric mosaics", "ornate carvings", "detailed reliefs"],
        "colors": ["gold accents", "rich blues", "deep reds", "ivory white"]
    },
    
    "elven": {
        "name": "Elven",
        "description": "The structures are of elven architecture with lots of wood on the structures and curved roofs. Graceful, flowing lines characterize the design, with organic shapes that seem to grow from nature itself. Tall, slender towers reach skyward, while curved eaves and flowing rooflines create an ethereal appearance. Living wood and crystal elements integrate seamlessly with traditional construction.",
        "materials": ["living wood", "crystal", "silver accents", "natural stone"],
        "features": ["curved roofs", "flowing lines", "tall spires", "organic shapes"],
        "colors": ["forest green", "silver", "natural wood", "crystal blue"]
    },
    
    "orcish": {
        "name": "Orcish", 
        "description": "Metal, wood and spike decorate the outside of all the structures in this style. Brutal and intimidating architecture dominates, with heavy iron reinforcements and aggressive spikes protruding from walls and battlements. Roughly hewn timber combines with crude metalwork, creating structures that prioritize function and fear over beauty.",
        "materials": ["crude iron", "rough timber", "bone decorations", "dark stone"],
        "features": ["iron spikes", "heavy reinforcements", "brutal angles", "intimidating design"],
        "colors": ["dark iron", "blood red", "charcoal black", "rust brown"]
    },
    
    "human": {
        "name": "Human",
        "description": "Simple plain medieval architecture with wood and brick structures. Castles, parks, taverns, markets, churches, mansions, slums, favelas, and other human structures are present. Practical design emphasizes functionality while maintaining modest decorative elements. Stone foundations support timber-framed upper stories, with thatched or tiled roofs completing the traditional appearance.",
        "materials": ["timber framing", "brick", "thatch", "clay tiles", "rough stone"],
        "features": ["practical design", "timber framing", "modest decoration", "functional layout"],
        "colors": ["natural wood", "red brick", "earth tones", "grey stone"]
    },
    
    # Additional styles (5 new ones)
    "crystalline": {
        "name": "Crystalline",
        "description": "Structures appear to be carved from massive crystals or grown from crystal formations. Geometric faceted surfaces catch and refract light, creating prismatic effects throughout the architecture. Translucent walls glow with inner light, while crystal spires twist skyward in impossible helical formations. The entire structure seems to resonate with harmonic frequencies.",
        "materials": ["pure crystal", "prismatic glass", "light-conducting stone", "ethereal metal"],
        "features": ["faceted surfaces", "light refraction", "crystal spires", "geometric forms"],
        "colors": ["prismatic", "clear crystal", "rainbow reflections", "pure white"]
    },
    
    "steampunk": {
        "name": "Steampunk",
        "description": "Industrial Victorian architecture enhanced with brass pipes, copper fittings, and steam-powered mechanisms. Gears, pistons, and clockwork elements are integrated into the structural design. Smokestacks and steam vents emerge from rooftops, while elaborate pipe networks snake along exterior walls. The aesthetic combines mechanical ingenuity with ornate Victorian sensibilities.",
        "materials": ["brass", "copper pipes", "wrought iron", "tarnished metal", "industrial glass"],
        "features": ["gear mechanisms", "steam pipes", "clockwork elements", "industrial details"],
        "colors": ["brass gold", "copper green", "rust red", "steam white"]
    },
    
    "biomechanical": {
        "name": "Biomechanical",
        "description": "Architecture that blends organic biological forms with mechanical structures. Walls pulse with organic rhythms while mechanical joints and hydraulic systems provide structural support. Surfaces appear to breathe and grow, with bio-luminescent elements providing lighting. The boundary between living tissue and machine becomes indistinguishable.",
        "materials": ["living metal", "organic composites", "bio-luminescent elements", "flexible membranes"],
        "features": ["organic curves", "mechanical joints", "pulsing surfaces", "bio-integrated systems"],
        "colors": ["bio-luminescent blue", "organic pink", "metallic grey", "living green"]
    },
    
    "celestial": {
        "name": "Celestial",
        "description": "Divine architecture that seems to channel the heavens themselves. Floating elements defy gravity while starlight patterns are carved into marble surfaces. Golden halos crown spires that reach toward the sky, and ethereal bridges span impossible distances. The entire structure radiates divine light and inspirational majesty.",
        "materials": ["white marble", "gold inlay", "starlight crystal", "ethereal energy"],
        "features": ["floating elements", "divine light", "star patterns", "ethereal bridges"],
        "colors": ["pure white", "celestial gold", "starlight silver", "divine blue"]
    },
    
    "volcanic": {
        "name": "Volcanic",
        "description": "Architecture forged from the fury of volcanic forces. Obsidian walls gleam like black glass, while molten rock flows are channeled through architectural features. Lava fountains provide both light and heat, creating a dramatic and dangerous aesthetic. The structures appear to emerge from volcanic rock formations, with glowing fissures revealing the fiery power within.",
        "materials": ["obsidian", "volcanic rock", "molten metal", "heat-resistant stone"],
        "features": ["lava channels", "obsidian surfaces", "volcanic vents", "glowing fissures"],
        "colors": ["volcanic black", "molten orange", "lava red", "ash grey"]
    }
}

def get_style_description(style_name: str) -> str:
    """Get the detailed description for an architectural style."""
    style = ARCHITECTURAL_STYLES.get(style_name.lower(), None)
    if style:
        return style["description"]
    else:
        logger.warning(f"Unknown architectural style: {style_name}")
        return f"Unknown style: {style_name}. Using default architecture."

def get_style_materials(style_name: str) -> List[str]:
    """Get the materials associated with an architectural style."""
    style = ARCHITECTURAL_STYLES.get(style_name.lower(), None)
    return style["materials"] if style else ["default materials"]

def get_style_features(style_name: str) -> List[str]:
    """Get the architectural features associated with a style."""
    style = ARCHITECTURAL_STYLES.get(style_name.lower(), None)
    return style["features"] if style else ["default features"]

def get_style_colors(style_name: str) -> List[str]:
    """Get the color palette associated with an architectural style."""
    style = ARCHITECTURAL_STYLES.get(style_name.lower(), None)
    return style["colors"] if style else ["default colors"]

def list_available_styles() -> List[str]:
    """Get a list of all available architectural style names."""
    return list(ARCHITECTURAL_STYLES.keys())

def get_style_info(style_name: str) -> Dict[str, Any]:
    """Get complete information about an architectural style."""
    style = ARCHITECTURAL_STYLES.get(style_name.lower(), None)
    if style:
        return style.copy()
    else:
        return {
            "name": "Unknown",
            "description": f"Unknown style: {style_name}",
            "materials": ["default materials"],
            "features": ["default features"],
            "colors": ["default colors"]
        }

def enhance_prompt_with_style(base_prompt: str, style_name: str) -> str:
    """Enhance a building prompt with architectural style descriptions."""
    if not style_name or style_name.lower() == "none":
        return base_prompt
    
    style_description = get_style_description(style_name)
    materials = get_style_materials(style_name)
    features = get_style_features(style_name)
    
    enhanced_prompt = f"{base_prompt}\n\nArchitectural Style: {style_name.title()}\n"
    enhanced_prompt += f"Style Description: {style_description}\n"
    enhanced_prompt += f"Key Materials: {', '.join(materials)}\n"
    enhanced_prompt += f"Architectural Features: {', '.join(features)}\n"
    
    return enhanced_prompt

def get_style_summary() -> str:
    """Get a summary of all available architectural styles."""
    summary = "Available Architectural Styles:\n\n"
    for style_name, style_data in ARCHITECTURAL_STYLES.items():
        summary += f"• {style_data['name']}: {style_data['description'][:100]}...\n"
    return summary
