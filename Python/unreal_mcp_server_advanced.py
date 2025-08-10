"""
Unreal Engine Advanced MCP Server

A streamlined MCP server focused on advanced composition tools for Unreal Engine.
Contains only the advanced tools from the expanded MCP tool system to keep tool count manageable.
"""

import logging
import socket
import sys
import json
import math
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP, Context

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('unreal_mcp_advanced.log'),
    ]
)
logger = logging.getLogger("UnrealMCP_Advanced")

# Configuration
UNREAL_HOST = "127.0.0.1"
UNREAL_PORT = 55557

class UnrealConnection:
    """Connection to an Unreal Engine instance."""
    
    def __init__(self):
        """Initialize the connection."""
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the Unreal Engine instance."""
        try:
            # Close any existing socket
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            logger.info(f"Connecting to Unreal at {UNREAL_HOST}:{UNREAL_PORT}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            
            # Set socket options for better stability
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
            self.socket.connect((UNREAL_HOST, UNREAL_PORT))
            self.connected = True
            logger.info("Connected to Unreal Engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Unreal: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the Unreal Engine instance."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        self.connected = False

    def receive_full_response(self, sock, buffer_size=4096) -> bytes:
        """Receive a complete response from Unreal, handling chunked data."""
        chunks = []
        sock.settimeout(30)
        try:
            while True:
                chunk = sock.recv(buffer_size)
                if not chunk:
                    if not chunks:
                        raise Exception("Connection closed before receiving data")
                    break
                chunks.append(chunk)
                
                # Process the data received so far
                data = b''.join(chunks)
                decoded_data = data.decode('utf-8')
                
                # Try to parse as JSON to check if complete
                try:
                    json.loads(decoded_data)
                    logger.info(f"Received complete response ({len(data)} bytes)")
                    return data
                except json.JSONDecodeError:
                    # Not complete JSON yet, continue reading
                    logger.debug(f"Received partial response, waiting for more data...")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing response chunk: {str(e)}")
                    continue
        except socket.timeout:
            logger.warning("Socket timeout during receive")
            if chunks:
                data = b''.join(chunks)
                try:
                    json.loads(data.decode('utf-8'))
                    logger.info(f"Using partial response after timeout ({len(data)} bytes)")
                    return data
                except:
                    pass
            raise Exception("Timeout receiving Unreal response")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
    
    def send_command(self, command: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Send a command to Unreal Engine and get the response."""
        # Always reconnect for each command
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
        
        if not self.connect():
            logger.error("Failed to connect to Unreal Engine for command")
            return None
        
        try:
            command_obj = {
                "type": command,
                "params": params or {}
            }
            
            command_json = json.dumps(command_obj)
            logger.info(f"Sending command: {command_json}")
            self.socket.sendall(command_json.encode('utf-8'))
            
            response_data = self.receive_full_response(self.socket)
            response = json.loads(response_data.decode('utf-8'))
            
            logger.info(f"Complete response from Unreal: {response}")
            
            # Handle error responses
            if response.get("status") == "error":
                error_message = response.get("error") or response.get("message", "Unknown Unreal error")
                logger.error(f"Unreal error (status=error): {error_message}")
                if "error" not in response:
                    response["error"] = error_message
            elif response.get("success") is False:
                error_message = response.get("error") or response.get("message", "Unknown Unreal error")
                logger.error(f"Unreal error (success=false): {error_message}")
                response = {
                    "status": "error",
                    "error": error_message
                }
            
            # Always close the connection after command
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.connected = False
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            return {
                "status": "error",
                "error": str(e)
            }

# Global connection state
_unreal_connection: UnrealConnection = None

def get_unreal_connection() -> Optional[UnrealConnection]:
    """Get the connection to Unreal Engine."""
    global _unreal_connection
    try:
        if _unreal_connection is None:
            _unreal_connection = UnrealConnection()
            if not _unreal_connection.connect():
                logger.warning("Could not connect to Unreal Engine")
                _unreal_connection = None
        return _unreal_connection
    except Exception as e:
        logger.error(f"Error getting Unreal connection: {e}")
        return None

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Handle server startup and shutdown."""
    global _unreal_connection
    logger.info("UnrealMCP Advanced server starting up")
    try:
        _unreal_connection = get_unreal_connection()
        if _unreal_connection:
            logger.info("Connected to Unreal Engine on startup")
        else:
            logger.warning("Could not connect to Unreal Engine on startup")
    except Exception as e:
        logger.error(f"Error connecting to Unreal Engine on startup: {e}")
        _unreal_connection = None
    
    try:
        yield {}
    finally:
        if _unreal_connection:
            _unreal_connection.disconnect()
            _unreal_connection = None
        logger.info("Unreal MCP Advanced server shut down")

# Initialize server
mcp = FastMCP(
    "UnrealMCP_Advanced",
    description="Unreal Engine Advanced Tools - Streamlined MCP server for advanced composition and building tools",
    lifespan=server_lifespan
)

# Essential Actor Management Tools
@mcp.tool()
def get_actors_in_level(random_string: str = "") -> Dict[str, Any]:
    """Get a list of all actors in the current level."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        response = unreal.send_command("get_actors_in_level", {})
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"get_actors_in_level error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def find_actors_by_name(pattern: str) -> Dict[str, Any]:
    """Find actors by name pattern."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        response = unreal.send_command("find_actors_by_name", {"pattern": pattern})
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"find_actors_by_name error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def spawn_actor(
    name: str,
    type: str,
    location: List[float] = [0, 0, 0],
    rotation: List[float] = [0, 0, 0]
) -> Dict[str, Any]:
    """Create a new actor in the current level."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {
            "name": name,
            "type": type,
            "location": location,
            "rotation": rotation
        }
        response = unreal.send_command("spawn_actor", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"spawn_actor error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def delete_actor(name: str) -> Dict[str, Any]:
    """Delete an actor by name."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        response = unreal.send_command("delete_actor", {"name": name})
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"delete_actor error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def set_actor_transform(
    name: str,
    location: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None
) -> Dict[str, Any]:
    """Set the transform of an actor."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {"name": name}
        if location is not None:
            params["location"] = location
        if rotation is not None:
            params["rotation"] = rotation
        if scale is not None:
            params["scale"] = scale
            
        response = unreal.send_command("set_actor_transform", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"set_actor_transform error: {e}")
        return {"success": False, "message": str(e)}

# Essential Blueprint Tools for Physics Actors
@mcp.tool()
def create_blueprint(name: str, parent_class: str) -> Dict[str, Any]:
    """Create a new Blueprint class."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {
            "name": name,
            "parent_class": parent_class
        }
        response = unreal.send_command("create_blueprint", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"create_blueprint error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def add_component_to_blueprint(
    blueprint_name: str,
    component_type: str,
    component_name: str,
    location: List[float] = [],
    rotation: List[float] = [],
    scale: List[float] = [],
    component_properties: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """Add a component to a Blueprint."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {
            "blueprint_name": blueprint_name,
            "component_type": component_type,
            "component_name": component_name,
            "location": location,
            "rotation": rotation,
            "scale": scale,
            "component_properties": component_properties
        }
        response = unreal.send_command("add_component_to_blueprint", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"add_component_to_blueprint error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def set_static_mesh_properties(
    blueprint_name: str,
    component_name: str,
    static_mesh: str = "/Engine/BasicShapes/Cube.Cube"
) -> Dict[str, Any]:
    """Set static mesh properties on a StaticMeshComponent."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "static_mesh": static_mesh
        }
        response = unreal.send_command("set_static_mesh_properties", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"set_static_mesh_properties error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def set_physics_properties(
    blueprint_name: str,
    component_name: str,
    simulate_physics: bool = True,
    gravity_enabled: bool = True,
    mass: float = 1,
    linear_damping: float = 0.01,
    angular_damping: float = 0
) -> Dict[str, Any]:
    """Set physics properties on a component."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "simulate_physics": simulate_physics,
            "gravity_enabled": gravity_enabled,
            "mass": mass,
            "linear_damping": linear_damping,
            "angular_damping": angular_damping
        }
        response = unreal.send_command("set_physics_properties", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"set_physics_properties error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def compile_blueprint(blueprint_name: str) -> Dict[str, Any]:
    """Compile a Blueprint."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {"blueprint_name": blueprint_name}
        response = unreal.send_command("compile_blueprint", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"compile_blueprint error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def spawn_blueprint_actor(
    blueprint_name: str,
    actor_name: str,
    location: List[float] = [0, 0, 0],
    rotation: List[float] = [0, 0, 0]
) -> Dict[str, Any]:
    """Spawn an actor from a Blueprint."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        params = {
            "blueprint_name": blueprint_name,
            "actor_name": actor_name,
            "location": location,
            "rotation": rotation
        }
        response = unreal.send_command("spawn_blueprint_actor", params)
        return response or {"success": False, "message": "No response from Unreal"}
    except Exception as e:
        logger.error(f"spawn_blueprint_actor error: {e}")
        return {"success": False, "message": str(e)}

# Advanced Composition Tools
@mcp.tool()
def create_pyramid(
    base_size: int = 3,
    block_size: float = 100.0,
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "PyramidBlock",
    mesh: str = "/Engine/BasicShapes/Cube.Cube"
) -> Dict[str, Any]:
    """Spawn a pyramid made of cube actors."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        spawned = []
        scale = block_size / 100.0
        for level in range(base_size):
            count = base_size - level
            for x in range(count):
                for y in range(count):
                    actor_name = f"{name_prefix}_{level}_{x}_{y}"
                    loc = [
                        location[0] + (x - (count - 1)/2) * block_size,
                        location[1] + (y - (count - 1)/2) * block_size,
                        location[2] + level * block_size
                    ]
                    params = {
                        "name": actor_name,
                        "type": "StaticMeshActor",
                        "location": loc,
                        "scale": [scale, scale, scale],
                        "static_mesh": mesh
                    }
                    resp = unreal.send_command("spawn_actor", params)
                    if resp:
                        spawned.append(resp)
        return {"success": True, "actors": spawned}
    except Exception as e:
        logger.error(f"create_pyramid error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_wall(
    length: int = 5,
    height: int = 2,
    block_size: float = 100.0,
    location: List[float] = [0.0, 0.0, 0.0],
    orientation: str = "x",
    name_prefix: str = "WallBlock",
    mesh: str = "/Engine/BasicShapes/Cube.Cube"
) -> Dict[str, Any]:
    """Create a simple wall from cubes."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        spawned = []
        scale = block_size / 100.0
        for h in range(height):
            for i in range(length):
                actor_name = f"{name_prefix}_{h}_{i}"
                if orientation == "x":
                    loc = [location[0] + i * block_size, location[1], location[2] + h * block_size]
                else:
                    loc = [location[0], location[1] + i * block_size, location[2] + h * block_size]
                params = {
                    "name": actor_name,
                    "type": "StaticMeshActor",
                    "location": loc,
                    "scale": [scale, scale, scale],
                    "static_mesh": mesh
                }
                resp = unreal.send_command("spawn_actor", params)
                if resp:
                    spawned.append(resp)
        return {"success": True, "actors": spawned}
    except Exception as e:
        logger.error(f"create_wall error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_tower(
    height: int = 10,
    base_size: int = 4,
    block_size: float = 100.0,
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "TowerBlock",
    mesh: str = "/Engine/BasicShapes/Cube.Cube",
    tower_style: str = "cylindrical"  # "cylindrical", "square", "tapered"
) -> Dict[str, Any]:
    """Create a realistic tower with various architectural styles."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        spawned = []
        scale = block_size / 100.0

        for level in range(height):
            level_height = location[2] + level * block_size
            
            if tower_style == "cylindrical":
                # Create circular tower
                radius = (base_size / 2) * block_size  # Convert to world units (centimeters)
                circumference = 2 * math.pi * radius
                num_blocks = max(8, int(circumference / block_size))
                
                for i in range(num_blocks):
                    angle = (2 * math.pi * i) / num_blocks
                    x = location[0] + radius * math.cos(angle)
                    y = location[1] + radius * math.sin(angle)
                    
                    actor_name = f"{name_prefix}_{level}_{i}"
                    params = {
                        "name": actor_name,
                        "type": "StaticMeshActor",
                        "location": [x, y, level_height],
                        "scale": [scale, scale, scale],
                        "static_mesh": mesh
                    }
                    resp = unreal.send_command("spawn_actor", params)
                    if resp:
                        spawned.append(resp)
                        
            elif tower_style == "tapered":
                # Create tapering square tower
                current_size = max(1, base_size - (level // 2))
                half_size = current_size / 2
                
                # Create walls for current level
                for side in range(4):
                    for i in range(current_size):
                        if side == 0:  # Front wall
                            x = location[0] + (i - half_size + 0.5) * block_size
                            y = location[1] - half_size * block_size
                            actor_name = f"{name_prefix}_{level}_front_{i}"
                        elif side == 1:  # Right wall
                            x = location[0] + half_size * block_size
                            y = location[1] + (i - half_size + 0.5) * block_size
                            actor_name = f"{name_prefix}_{level}_right_{i}"
                        elif side == 2:  # Back wall
                            x = location[0] + (half_size - i - 0.5) * block_size
                            y = location[1] + half_size * block_size
                            actor_name = f"{name_prefix}_{level}_back_{i}"
                        else:  # Left wall
                            x = location[0] - half_size * block_size
                            y = location[1] + (half_size - i - 0.5) * block_size
                            actor_name = f"{name_prefix}_{level}_left_{i}"
                            
                        params = {
                            "name": actor_name,
                            "type": "StaticMeshActor",
                            "location": [x, y, level_height],
                            "scale": [scale, scale, scale],
                            "static_mesh": mesh
                        }
                        resp = unreal.send_command("spawn_actor", params)
                        if resp:
                            spawned.append(resp)
                            
            else:  # square tower
                # Create square tower walls
                half_size = base_size / 2
                
                # Four walls
                for side in range(4):
                    for i in range(base_size):
                        if side == 0:  # Front wall
                            x = location[0] + (i - half_size + 0.5) * block_size
                            y = location[1] - half_size * block_size
                            actor_name = f"{name_prefix}_{level}_front_{i}"
                        elif side == 1:  # Right wall
                            x = location[0] + half_size * block_size
                            y = location[1] + (i - half_size + 0.5) * block_size
                            actor_name = f"{name_prefix}_{level}_right_{i}"
                        elif side == 2:  # Back wall
                            x = location[0] + (half_size - i - 0.5) * block_size
                            y = location[1] + half_size * block_size
                            actor_name = f"{name_prefix}_{level}_back_{i}"
                        else:  # Left wall
                            x = location[0] - half_size * block_size
                            y = location[1] + (half_size - i - 0.5) * block_size
                            actor_name = f"{name_prefix}_{level}_left_{i}"
                            
                        params = {
                            "name": actor_name,
                            "type": "StaticMeshActor",
                            "location": [x, y, level_height],
                            "scale": [scale, scale, scale],
                            "static_mesh": mesh
                        }
                        resp = unreal.send_command("spawn_actor", params)
                        if resp:
                            spawned.append(resp)
                            
            # Add decorative elements every few levels
            if level % 3 == 2 and level < height - 1:
                # Add corner details
                for corner in range(4):
                    angle = corner * math.pi / 2
                    detail_x = location[0] + (base_size/2 + 0.5) * block_size * math.cos(angle)
                    detail_y = location[1] + (base_size/2 + 0.5) * block_size * math.sin(angle)
                    
                    actor_name = f"{name_prefix}_{level}_detail_{corner}"
                    params = {
                        "name": actor_name,
                        "type": "StaticMeshActor",
                        "location": [detail_x, detail_y, level_height],
                        "scale": [scale * 0.7, scale * 0.7, scale * 0.7],
                        "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                    }
                    resp = unreal.send_command("spawn_actor", params)
                    if resp:
                        spawned.append(resp)
                        
        return {"success": True, "actors": spawned, "tower_style": tower_style}
    except Exception as e:
        logger.error(f"create_tower error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_staircase(
    steps: int = 5,
    step_size: List[float] = [100.0, 100.0, 50.0],
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "Stair",
    mesh: str = "/Engine/BasicShapes/Cube.Cube"
) -> Dict[str, Any]:
    """Create a staircase from cubes."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        spawned = []
        sx, sy, sz = step_size
        for i in range(steps):
            actor_name = f"{name_prefix}_{i}"
            loc = [location[0] + i * sx, location[1], location[2] + i * sz]
            scale = [sx/100.0, sy/100.0, sz/100.0]
            params = {
                "name": actor_name,
                "type": "StaticMeshActor",
                "location": loc,
                "scale": scale,
                "static_mesh": mesh
            }
            resp = unreal.send_command("spawn_actor", params)
            if resp:
                spawned.append(resp)
        return {"success": True, "actors": spawned}
    except Exception as e:
        logger.error(f"create_staircase error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def construct_house(
    width: int = 1200,
    depth: int = 1000,
    height: int = 600,
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "House",
    mesh: str = "/Engine/BasicShapes/Cube.Cube",
    house_style: str = "modern"  # "modern", "cottage", "mansion"
) -> Dict[str, Any]:
    """Construct a realistic house with architectural details and multiple rooms."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
        results = []
        wall_thickness = 20.0  # Thinner walls for realism
        floor_thickness = 30.0
        
        # Adjust dimensions based on style
        if house_style == "mansion":
            width = int(width * 1.5)
            depth = int(depth * 1.5)
            height = int(height * 1.3)
        elif house_style == "cottage":
            width = int(width * 0.8)
            depth = int(depth * 0.8)
            height = int(height * 0.9)
        
        # Create foundation as single large block
        foundation_params = {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - floor_thickness/2],
            "scale": [(width + 200)/100.0, (depth + 200)/100.0, floor_thickness/100.0],
            "static_mesh": mesh
        }
        foundation_resp = unreal.send_command("spawn_actor", foundation_params)
        if foundation_resp:
            results.append(foundation_resp)
        
        # Create floor as single piece
        floor_params = {
            "name": f"{name_prefix}_Floor",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + floor_thickness/2],
            "scale": [width/100.0, depth/100.0, floor_thickness/100.0],
            "static_mesh": mesh
        }
        floor_resp = unreal.send_command("spawn_actor", floor_params)
        if floor_resp:
            results.append(floor_resp)
        
        base_z = location[2] + floor_thickness
        
        # Create walls as large segments
        # Front wall (with door opening)
        door_width = 120.0
        door_height = 240.0
        
        # Front wall - left side of door
        front_left_width = (width/2 - door_width/2)
        front_left_params = {
            "name": f"{name_prefix}_FrontWall_Left",
            "type": "StaticMeshActor",
            "location": [location[0] - width/4 - door_width/4, location[1] - depth/2, base_z + height/2],
            "scale": [front_left_width/100.0, wall_thickness/100.0, height/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", front_left_params)
        if resp:
            results.append(resp)
        
        # Front wall - right side of door
        front_right_params = {
            "name": f"{name_prefix}_FrontWall_Right",
            "type": "StaticMeshActor",
            "location": [location[0] + width/4 + door_width/4, location[1] - depth/2, base_z + height/2],
            "scale": [front_left_width/100.0, wall_thickness/100.0, height/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", front_right_params)
        if resp:
            results.append(resp)
        
        # Front wall - above door
        front_top_params = {
            "name": f"{name_prefix}_FrontWall_Top",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2, base_z + door_height + (height - door_height)/2],
            "scale": [door_width/100.0, wall_thickness/100.0, (height - door_height)/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", front_top_params)
        if resp:
            results.append(resp)
        
        # Back wall with window openings
        window_width = 150.0
        window_height = 150.0
        window_y = base_z + height/2
        
        # Back wall - left section
        back_left_params = {
            "name": f"{name_prefix}_BackWall_Left",
            "type": "StaticMeshActor",
            "location": [location[0] - width/3, location[1] + depth/2, base_z + height/2],
            "scale": [width/3/100.0, wall_thickness/100.0, height/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", back_left_params)
        if resp:
            results.append(resp)
        
        # Back wall - center section (with window cutouts)
        back_center_bottom_params = {
            "name": f"{name_prefix}_BackWall_Center_Bottom",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] + depth/2, base_z + (window_y - window_height/2 - base_z)/2],
            "scale": [width/3/100.0, wall_thickness/100.0, (window_y - window_height/2 - base_z)/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", back_center_bottom_params)
        if resp:
            results.append(resp)
        
        back_center_top_params = {
            "name": f"{name_prefix}_BackWall_Center_Top",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] + depth/2, window_y + window_height/2 + (base_z + height - window_y - window_height/2)/2],
            "scale": [width/3/100.0, wall_thickness/100.0, (base_z + height - window_y - window_height/2)/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", back_center_top_params)
        if resp:
            results.append(resp)
        
        # Back wall - right section
        back_right_params = {
            "name": f"{name_prefix}_BackWall_Right",
            "type": "StaticMeshActor",
            "location": [location[0] + width/3, location[1] + depth/2, base_z + height/2],
            "scale": [width/3/100.0, wall_thickness/100.0, height/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", back_right_params)
        if resp:
            results.append(resp)
        
        # Left wall
        left_wall_params = {
            "name": f"{name_prefix}_LeftWall",
            "type": "StaticMeshActor",
            "location": [location[0] - width/2, location[1], base_z + height/2],
            "scale": [wall_thickness/100.0, depth/100.0, height/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", left_wall_params)
        if resp:
            results.append(resp)
        
        # Right wall  
        right_wall_params = {
            "name": f"{name_prefix}_RightWall",
            "type": "StaticMeshActor",
            "location": [location[0] + width/2, location[1], base_z + height/2],
            "scale": [wall_thickness/100.0, depth/100.0, height/100.0],
            "static_mesh": mesh
        }
        resp = unreal.send_command("spawn_actor", right_wall_params)
        if resp:
            results.append(resp)
        
                    # Create flat roof
            roof_thickness = 30.0
            roof_overhang = 100.0
            
            # Single flat roof piece covering the entire house
            flat_roof_params = {
                "name": f"{name_prefix}_Roof",
                "type": "StaticMeshActor",
                "location": [
                    location[0],
                    location[1],
                    base_z + height + roof_thickness/2
                ],
                "rotation": [0, 0, 0],  # No rotation - flat roof
                "scale": [(width + roof_overhang*2)/100.0, (depth + roof_overhang*2)/100.0, roof_thickness/100.0],
                "static_mesh": mesh
            }
            resp = unreal.send_command("spawn_actor", flat_roof_params)
            if resp:
                results.append(resp)
        
                    # Add chimney for cottage/mansion styles
            if house_style in ["cottage", "mansion"]:
                chimney_params = {
                    "name": f"{name_prefix}_Chimney",
                    "type": "StaticMeshActor",
                    "location": [
                        location[0] + width/3,
                        location[1] + depth/3,
                        base_z + height + roof_thickness + 150  # Position above flat roof
                    ],
                    "scale": [1.0, 1.0, 2.5],
                    "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                }
                resp = unreal.send_command("spawn_actor", chimney_params)
                if resp:
                    results.append(resp)
        
        # Add porch for mansion style
        if house_style == "mansion":
            # Porch floor
            porch_floor_params = {
                "name": f"{name_prefix}_Porch_Floor",
                "type": "StaticMeshActor",
                "location": [location[0], location[1] - depth/2 - 150, location[2]],
                "scale": [width/100.0, 3.0, 0.3],
                "static_mesh": mesh
            }
            resp = unreal.send_command("spawn_actor", porch_floor_params)
            if resp:
                results.append(resp)
            
            # Porch columns
            for i, x_offset in enumerate([-width/3, 0, width/3]):
                column_params = {
                    "name": f"{name_prefix}_Porch_Column_{i}",
                    "type": "StaticMeshActor",
                    "location": [
                        location[0] + x_offset,
                        location[1] - depth/2 - 250,
                        base_z + height/2
                    ],
                    "scale": [0.5, 0.5, height/100.0],
                    "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                }
                resp = unreal.send_command("spawn_actor", column_params)
                if resp:
                    results.append(resp)
            
                            # Porch roof
                porch_roof_params = {
                    "name": f"{name_prefix}_Porch_Roof",
                    "type": "StaticMeshActor",
                    "location": [location[0], location[1] - depth/2 - 150, base_z + height - 50],
                    "scale": [(width + 100)/100.0, 4.0, 0.3],  # Consistent thickness with main roof
                    "static_mesh": mesh
                }
                resp = unreal.send_command("spawn_actor", porch_roof_params)
                if resp:
                    results.append(resp)
        
        # Add details based on style
        if house_style == "modern":
            # Add garage door
            garage_params = {
                "name": f"{name_prefix}_Garage_Door",
                "type": "StaticMeshActor",
                "location": [location[0] - width/3, location[1] - depth/2 + wall_thickness/2, base_z + 150],
                "scale": [2.5, 0.1, 2.5],
                "static_mesh": mesh
            }
            resp = unreal.send_command("spawn_actor", garage_params)
            if resp:
                results.append(resp)
        
        return {
            "success": True,
            "actors": results,
            "house_style": house_style,
            "dimensions": {"width": width, "depth": depth, "height": height},
            "features": [
                "foundation", "floor", "walls", "windows", "door", "flat_roof"
            ] + (["chimney"] if house_style in ["cottage", "mansion"] else []) + 
                (["porch", "columns"] if house_style == "mansion" else []) +
                (["garage"] if house_style == "modern" else []),
            "total_actors": len(results)
        }
    except Exception as e:
        logger.error(f"construct_house error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_arch(
    radius: float = 300.0,
    segments: int = 6,
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "ArchBlock",
    mesh: str = "/Engine/BasicShapes/Cube.Cube"
) -> Dict[str, Any]:
    """Create a simple arch using cubes in a semicircle."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        spawned = []
        angle_step = math.pi / segments
        scale = radius / 300.0 / 2
        for i in range(segments + 1):
            theta = angle_step * i
            x = radius * math.cos(theta)
            z = radius * math.sin(theta)
            actor_name = f"{name_prefix}_{i}"
            params = {
                "name": actor_name,
                "type": "StaticMeshActor",
                "location": [location[0] + x, location[1], location[2] + z],
                "scale": [scale, scale, scale],
                "static_mesh": mesh
            }
            resp = unreal.send_command("spawn_actor", params)
            if resp:
                spawned.append(resp)
        return {"success": True, "actors": spawned}
    except Exception as e:
        logger.error(f"create_arch error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def spawn_physics_actor(
    name: str,
    mesh_path: str = "/Engine/BasicShapes/Cube.Cube",
    location: List[float] = [0.0, 0.0, 0.0],
    mass: float = 1.0,
    simulate_physics: bool = True,
    gravity_enabled: bool = True,
    color: List[float] = None,  # Optional color parameter [R, G, B, A]
    scale: List[float] = [1.0, 1.0, 1.0]  # Default scale
) -> Dict[str, Any]:
    """Spawn an actor with physics properties using a temporary Blueprint."""
    try:
        bp_name = f"{name}_BP"
        create_blueprint(bp_name, "Actor")
        add_component_to_blueprint(bp_name, "StaticMeshComponent", "Mesh", scale=scale)
        set_static_mesh_properties(bp_name, "Mesh", mesh_path)
        set_physics_properties(bp_name, "Mesh", simulate_physics, gravity_enabled, mass)
        
        # Set color if provided
        if color is not None:
            set_mesh_material_color(bp_name, "Mesh", color)
        
        compile_blueprint(bp_name)
        result = spawn_blueprint_actor(bp_name, name, location)
        
        # Ensure proper scale is set on the spawned actor
        if result.get("success", False):
            spawned_name = result.get("result", {}).get("name", name)
            set_actor_transform(spawned_name, scale=scale)
        
        return result
    except Exception as e:
        logger.error(f"spawn_physics_actor error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_bouncy_ball(
    name: str,
    location: List[float] = [0.0, 0.0, 0.0],
    color: List[float] = [1.0, 0.0, 0.0, 1.0],  # Default red color
    size: float = 2.0  # Default size multiplier
) -> Dict[str, Any]:
    """Convenience function to spawn a bouncing sphere with color and size control."""
    try:
        # Create the physics blueprint
        bp_name = f"{name}_BP"
        
        # Create blueprint
        create_result = create_blueprint(bp_name, "Actor")
        if not create_result.get("success", False):
            return {"success": False, "message": f"Failed to create blueprint: {create_result.get('message', 'Unknown error')}"}
        
        # Add mesh component
        add_comp_result = add_component_to_blueprint(bp_name, "StaticMeshComponent", "Mesh")
        if not add_comp_result.get("success", False):
            return {"success": False, "message": f"Failed to add component: {add_comp_result.get('message', 'Unknown error')}"}
        
        # Set sphere mesh
        mesh_result = set_static_mesh_properties(bp_name, "Mesh", "/Engine/BasicShapes/Sphere.Sphere")
        if not mesh_result.get("success", False):
            return {"success": False, "message": f"Failed to set mesh: {mesh_result.get('message', 'Unknown error')}"}
        
        # Set physics properties for bouncing
        physics_result = set_physics_properties(
            bp_name, "Mesh", 
            simulate_physics=True, 
            gravity_enabled=True, 
            mass=1.0, 
            linear_damping=0.1,  # Some damping for realistic bouncing
            angular_damping=0.1
        )
        if not physics_result.get("success", False):
            return {"success": False, "message": f"Failed to set physics: {physics_result.get('message', 'Unknown error')}"}
        
        # Set color using the proven color system
        color_result = set_mesh_material_color(
            bp_name, 
            "Mesh", 
            color, 
            material_path="/Engine/BasicShapes/BasicShapeMaterial"
        )
        if not color_result.get("success", False):
            # Don't fail if color setting fails, just warn
            logger.warning(f"Failed to set color: {color_result.get('message', 'Unknown error')}")
        
        # Compile blueprint
        compile_result = compile_blueprint(bp_name)
        if not compile_result.get("success", False):
            return {"success": False, "message": f"Failed to compile blueprint: {compile_result.get('message', 'Unknown error')}"}
        
        # Spawn the actor with proper scale
        spawn_result = spawn_blueprint_actor(bp_name, name, location)
        if not spawn_result.get("success", False):
            return {"success": False, "message": f"Failed to spawn actor: {spawn_result.get('message', 'Unknown error')}"}
        
        # Get the actual spawned actor name from the response
        spawned_actor_name = spawn_result.get("result", {}).get("name", name)
        
        # Set the scale to make it visible and sized appropriately
        scale_result = set_actor_transform(spawned_actor_name, scale=[size, size, size])
        if not scale_result.get("success", False):
            logger.warning(f"Failed to set scale: {scale_result.get('message', 'Unknown error')}")
        
        return {
            "success": True,
            "actor": spawn_result.get("actor", {}),
            "color": color,
            "size": size,
            "message": f"Created bouncy ball '{name}' at {location} with color {color} and size {size}"
        }
        
    except Exception as e:
        logger.error(f"create_bouncy_ball error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_maze(
    rows: int = 8,
    cols: int = 8,
    cell_size: float = 300.0,
    wall_height: int = 3,
    location: List[float] = [0.0, 0.0, 0.0]
) -> Dict[str, Any]:
    """Create a proper solvable maze with entrance, exit, and guaranteed path using recursive backtracking algorithm."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
        import random
        spawned = []
        
        # Initialize maze grid - True means wall, False means open
        maze = [[True for _ in range(cols * 2 + 1)] for _ in range(rows * 2 + 1)]
        
        # Recursive backtracking maze generation
        def carve_path(row, col):
            # Mark current cell as path
            maze[row * 2 + 1][col * 2 + 1] = False
            
            # Random directions
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                
                # Check bounds
                if (0 <= new_row < rows and 0 <= new_col < cols and 
                    maze[new_row * 2 + 1][new_col * 2 + 1]):
                    
                    # Carve wall between current and new cell
                    maze[row * 2 + 1 + dr][col * 2 + 1 + dc] = False
                    carve_path(new_row, new_col)
        
        # Start carving from top-left corner
        carve_path(0, 0)
        
        # Create entrance and exit
        maze[1][0] = False  # Entrance on left side
        maze[rows * 2 - 1][cols * 2] = False  # Exit on right side
        
        # Build the actual maze in Unreal
        maze_height = rows * 2 + 1
        maze_width = cols * 2 + 1
        
        for r in range(maze_height):
            for c in range(maze_width):
                if maze[r][c]:  # If this is a wall
                    # Stack blocks to create wall height
                    for h in range(wall_height):
                        x_pos = location[0] + (c - maze_width/2) * cell_size
                        y_pos = location[1] + (r - maze_height/2) * cell_size
                        z_pos = location[2] + h * cell_size
                        
                        actor_name = f"Maze_Wall_{r}_{c}_{h}"
                        params = {
                            "name": actor_name,
                            "type": "StaticMeshActor",
                            "location": [x_pos, y_pos, z_pos],
                            "scale": [cell_size/100.0, cell_size/100.0, cell_size/100.0],
                            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                        }
                        resp = unreal.send_command("spawn_actor", params)
                        if resp:
                            spawned.append(resp)
        
        # Add entrance and exit markers
        entrance_marker = unreal.send_command("spawn_actor", {
            "name": "Maze_Entrance",
            "type": "StaticMeshActor",
            "location": [location[0] - maze_width/2 * cell_size - cell_size, 
                       location[1] + (-maze_height/2 + 1) * cell_size, 
                       location[2] + cell_size],
            "scale": [0.5, 0.5, 0.5],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if entrance_marker:
            spawned.append(entrance_marker)
            
        exit_marker = unreal.send_command("spawn_actor", {
            "name": "Maze_Exit",
            "type": "StaticMeshActor", 
            "location": [location[0] + maze_width/2 * cell_size + cell_size,
                       location[1] + (-maze_height/2 + rows * 2 - 1) * cell_size,
                       location[2] + cell_size],
            "scale": [0.5, 0.5, 0.5],
            "static_mesh": "/Engine/BasicShapes/Sphere.Sphere"
        })
        if exit_marker:
            spawned.append(exit_marker)
        
        return {
            "success": True, 
            "actors": spawned, 
            "maze_size": f"{rows}x{cols}",
            "wall_count": len([block for block in spawned if "Wall" in block.get("name", "")]),
            "entrance": "Left side (cylinder marker)",
            "exit": "Right side (sphere marker)"
        }
    except Exception as e:
        logger.error(f"create_maze error: {e}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def create_obstacle_course(
    checkpoints: int = 5,
    spacing: float = 500.0,
    location: List[float] = [0.0, 0.0, 0.0]
) -> Dict[str, Any]:
    """Create a simple obstacle course of pillars."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        spawned = []
        for i in range(checkpoints):
            actor_name = f"Obstacle_{i}"
            loc = [location[0] + i * spacing, location[1], location[2]]
            params = {
                "name": actor_name,
                "type": "StaticMeshActor",
                "location": loc,
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            }
            resp = unreal.send_command("spawn_actor", params)
            if resp:
                spawned.append(resp)
        return {"success": True, "actors": spawned}
    except Exception as e:
        logger.error(f"create_obstacle_course error: {e}")
        return {"success": False, "message": str(e)}

@mcp.prompt()
def info():
    """Information about available Unreal MCP Advanced tools and best practices."""
    return """
    # Unreal MCP Advanced Server Tools
    
    This streamlined server focuses on advanced composition and building tools for Unreal Engine.
    Total tools: ~25 (enhanced with architectural features + town generation)
    
    ## Essential Actor Management
    - `get_actors_in_level()` - List all actors in current level
    - `find_actors_by_name(pattern)` - Find actors by name pattern
    - `spawn_actor(name, type, location, rotation)` - Create basic actors
    - `delete_actor(name)` - Remove actors
    - `set_actor_transform(name, location, rotation, scale)` - Modify transforms
    
    ## Essential Blueprint Tools (for physics actors)
    - `create_blueprint(name, parent_class)` - Create Blueprint classes
    - `add_component_to_blueprint(blueprint_name, component_type, component_name)` - Add components
    - `set_static_mesh_properties(blueprint_name, component_name, static_mesh)` - Set meshes
    - `set_physics_properties(blueprint_name, component_name, ...)` - Configure physics
    - `compile_blueprint(blueprint_name)` - Compile changes
    - `spawn_blueprint_actor(blueprint_name, actor_name, location)` - Spawn from Blueprint
    - `set_mesh_material_color(blueprint_name, component_name, color, material_path, parameter_name)` - **NEW** Set colors on mesh components
    
    ## Advanced Composition Tools (Enhanced)
    - `create_pyramid(base_size, block_size, location, name_prefix, mesh)` - Build pyramids
    - `create_wall(length, height, block_size, location, orientation, name_prefix, mesh)` - Generate walls
    - `create_tower(height, base_size, block_size, location, name_prefix, mesh, tower_style)` - **ENHANCED** Architectural towers with styles: cylindrical, square, tapered + decorative elements
    - `create_staircase(steps, step_size, location, name_prefix, mesh)` - Build staircases
    - `construct_house(width, depth, height, location, name_prefix, mesh, house_style)` - **ENHANCED** Realistic houses with foundations, rooms, windows, doors, pitched roofs, chimneys (styles: modern, cottage, mansion)
    - `create_arch(radius, segments, location, name_prefix, mesh)` - Arch structures
    - `spawn_physics_actor(name, mesh_path, location, mass, simulate_physics, gravity_enabled)` - Physics objects
    - `create_bouncy_ball(name, location)` - Convenience bouncing sphere
    - `create_maze(rows, cols, cell_size, wall_height, location)` - **ENHANCED** Solvable mazes with recursive backtracking algorithm, entrance/exit markers
    - `create_obstacle_course(checkpoints, spacing, location)` - Obstacle courses
    - `spawn_mannequin(name, location, rotation, mannequin_type)` - **NEW** Spawn Unreal mannequins (types: default, manny, quinn) with fallbacks
    
    ## Ultimate Town Generation System (NEW!)
    - `create_town(town_size, building_density, location, name_prefix, include_infrastructure, architectural_style)` - **REVOLUTIONARY** Create complete dynamic towns with full infrastructure
    
    ## Enhanced Features
    
    ### Town Generation System (`create_town`) - The Crown Jewel
    This is the most advanced tool in the system, intelligently orchestrating all other tools to create living, breathing towns:
    
    **Town Sizes:**
    - **Small**: 3x3 blocks, ~15 buildings, residential focus
    - **Medium**: 5x5 blocks, ~35 buildings, mixed residential/commercial
    - **Large**: 7x7 blocks, ~60 buildings, urban environment
    - **Metropolis**: 10x10 blocks, ~100 buildings, dense cityscape
    
    **Dynamic Features:**
    - **Smart street grid**: Automatically creates intersecting streets with proper asphalt coloring
    - **Varied buildings**: Randomly places houses, mansions, towers, and commercial buildings
    - **Colorful infrastructure**: Street lights with warm lighting, colorful vehicles (red, blue, green, yellow, etc.)
    - **Living population**: Spawns mannequins throughout the town for realism
    - **Parks & nature**: Creates green spaces with brown tree trunks and green foliage
    - **Full randomization**: Every town generation creates unique layouts and building combinations
    
    **Building Variety:**
    - **Houses**: Randomly sized cottages and modern homes in browns/beiges
    - **Mansions**: Large luxury homes with porches and columns in whites/grays  
    - **Towers**: Cylindrical, square, or tapered towers in dark grays
    - **Commercial**: Office/store buildings in light grays
    
    **Infrastructure Elements:**
    - **Gray asphalt streets** in perfect grid pattern
    - **Street lights** with dark gray poles and warm white lights
    - **Colorful vehicles** randomly distributed on streets
    - **Green parks** with brown tree trunks and green spherical foliage
    - **Population** of varied mannequin types walking around
    
    ### Architectural Towers (`create_tower`)
    - **Cylindrical towers**: Circular arrangement of blocks
    - **Square towers**: Hollow square towers with proper walls
    - **Tapered towers**: Towers that narrow toward the top
    - **Decorative elements**: Corner details added every 3 levels
    
    ### Realistic Houses (`construct_house`)
    - **Foundations**: Proper foundation blocks beneath the house
    - **Multiple rooms**: Interior walls creating separate spaces
    - **Windows and doors**: Realistic openings with proper placement
    - **Flat roofs**: Clean flat roofing with proper overhang
    - **Chimneys**: Added for cottage and mansion styles
    - **Style variations**: Modern, cottage, and mansion with different proportions
    
    ### Solvable Mazes (`create_maze`)
    - **Guaranteed solution**: Uses recursive backtracking algorithm
    - **Entrance marker**: Cylinder marker at maze entrance
    - **Exit marker**: Sphere marker at maze exit
    - **Proper pathways**: No closed-off areas, always has solution path
    
    ### Mannequin Spawning (`spawn_mannequin`)
    - **Multiple attempts**: Tries various Unreal Engine mannequin asset paths
    - **Fallback options**: Falls back to static mesh if skeletal mesh fails
    - **Primitive fallback**: Creates basic humanoid using primitive shapes if no assets found
    - **Character types**: Supports manny, quinn, and default variations
    
    ### Color System (`set_mesh_material_color`)
    - **Full RGBA support**: [R, G, B, A] values from 0.0 to 1.0
    - **Common colors**: Red [1,0,0,1], Blue [0,0,1,1], Green [0,1,0,1], Yellow [1,1,0,1], etc.
    - **Material compatibility**: Works with Engine/BasicShapes/BasicShapeMaterial
    - **Parameter flexibility**: Supports BaseColor and Color parameters
    
    ## Best Practices
    
    ### Town Generation
    - **Start with create_town()** - This is the ultimate tool that showcases everything
    - **Experiment with sizes**: Try "small", "medium", "large", "metropolis"
    - **Adjust density**: Use 0.4-0.8 for realistic spacing, 1.0 for maximum density
    - **Try architectural styles**: "mixed" for variety, or "modern"/"cottage"/"mansion" for themed towns
    - **Enable infrastructure**: Always use include_infrastructure=True for complete towns
    - **Plan space**: Towns can be 3km+ wide (metropolis), ensure adequate space
    
    ### Advanced Composition
    - Use meaningful name_prefix values to organize generated objects
    - Plan locations to avoid overlapping structures
    - Consider performance implications of large compositions (metropolis = 500+ actors)
    - Use appropriate mesh paths for visual variety
    - Clean up test structures regularly
    - Take advantage of architectural styles for variety
    
    ### Color Usage
    - Apply colors before spawning for best results
    - Use realistic color palettes (browns for houses, grays for streets/towers)
    - Experiment with vibrant colors for vehicles and decorations
    - Always include alpha channel (1.0 for full opacity)
    
    ### Enhanced Features Usage
    - Try different tower_style values: "cylindrical", "square", "tapered"
    - Experiment with house_style options: "modern", "cottage", "mansion"
    - Use larger maze dimensions (8x8 or bigger) for interesting challenges
    - Place mannequins to populate your scenes with characters
    
    ### Physics Objects
    - Place physics actors above ground level to observe falling
    - Adjust mass values for realistic behavior
    - Use create_bouncy_ball for quick physics testing
    - Compile Blueprints after physics property changes
    
    ### Error Handling
    - Check command responses for success status
    - Use unique names to avoid conflicts
    - Validate parameters before complex operations
    - Handle Unreal Engine connection issues gracefully
    
    ### Performance Tips
    - Group related operations together
    - Use batched creation for large structures
    - Consider LOD implications for many objects (metropolis towns create 500+ actors)
    - Clean up temporary Blueprints when done
    - Be mindful of complex structures like detailed houses and large towns
    - Test with smaller towns first, then scale up to metropolis
    
    ## Quick Start Examples
    
    ### Create Your First Town
    ```
    create_town(town_size="medium", building_density=0.7, location=[0, 0, 0])
    ```
    
    ### Create a Large Mixed-Style Town
    ```
    create_town(town_size="large", building_density=0.8, architectural_style="mixed", include_infrastructure=True)
    ```
    
    ### Create a Mansion District
    ```
    create_town(town_size="small", building_density=0.5, architectural_style="mansion")
    ```
    """

@mcp.tool()
def spawn_mannequin(
    name: str = "Mannequin",
    location: List[float] = [0.0, 0.0, 0.0],
    rotation: List[float] = [0.0, 0.0, 0.0],
    mannequin_type: str = "default"  # "default", "manny", "quinn"
) -> Dict[str, Any]:
    """Spawn an Unreal Engine mannequin character at the specified location."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        
        # Determine which mannequin mesh to use
        mesh_path = "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"
        if mannequin_type.lower() == "manny":
            mesh_path = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
        elif mannequin_type.lower() == "quinn":
            mesh_path = "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"
        
        # Try common Unreal Engine mannequin paths
        possible_paths = [
            mesh_path,
            "/Game/Characters/Mannequins/Meshes/SKM_Quinn",
            "/Game/Characters/Mannequins/Meshes/SKM_Manny", 
            "/Engine/Characters/Mannequins/Meshes/SKM_Quinn",
            "/Engine/Characters/Mannequins/Meshes/SKM_Manny",
            "/Game/ThirdPerson/Characters/Mannequins/Meshes/SKM_Quinn_Simple",
            "/Game/ThirdPerson/Characters/Mannequins/Meshes/SKM_Manny_Simple"
        ]
        
        # Skip trying SkeletalMeshActor since it's not supported, go directly to StaticMeshActor
        logger.info("Trying to spawn mannequin as static mesh actor...")
        
        for mesh_path in possible_paths:
            params = {
                "name": f"{name}_{mannequin_type}_Static",
                "type": "StaticMeshActor", 
                "location": location,
                "rotation": rotation,
                "static_mesh": mesh_path
            }
            
            resp = unreal.send_command("spawn_actor", params)
            # Check for proper response format from Unreal
            if resp and resp.get("success") == True:
                return {
                    "success": True,
                    "actor": resp,
                    "mannequin_type": mannequin_type,
                    "mesh_used": mesh_path,
                    "message": f"Spawned {mannequin_type} mannequin as static mesh at {location}"
                }
            # If we get "Actor already exists" error, return early - don't try to create primitive humanoid
            elif resp and resp.get("success") == False and "already exists" in resp.get("message", ""):
                logger.warning(f"Actor {name}_{mannequin_type}_Static already exists, skipping...")
                return {
                    "success": True,  # This should be success since the actor already exists
                    "message": f"Mannequin {name}_{mannequin_type}_Static already exists"
                }
        
        # Final fallback: spawn a basic humanoid shape
        logger.info("Mannequin meshes not found, creating basic humanoid figure...")
        
        # Create basic humanoid using primitive shapes
        body_parts = []
        
        # Try to create each body part, but don't fail if some already exist
        parts_to_create = [
            (f"{name}_Body", [location[0], location[1], location[2] + 150], [0.8, 0.4, 1.5], "/Engine/BasicShapes/Cube.Cube"),
            (f"{name}_Head", [location[0], location[1], location[2] + 275], [0.5, 0.5, 0.5], "/Engine/BasicShapes/Sphere.Sphere"),
            (f"{name}_Arm_Left", [location[0], location[1] - 60, location[2] + 150], [0.3, 0.3, 1.2], "/Engine/BasicShapes/Cylinder.Cylinder"),
            (f"{name}_Arm_Right", [location[0], location[1] + 60, location[2] + 150], [0.3, 0.3, 1.2], "/Engine/BasicShapes/Cylinder.Cylinder"),
            (f"{name}_Leg_Left", [location[0], location[1] - 30, location[2] + 25], [0.3, 0.3, 1.0], "/Engine/BasicShapes/Cylinder.Cylinder"),
            (f"{name}_Leg_Right", [location[0], location[1] + 30, location[2] + 25], [0.3, 0.3, 1.0], "/Engine/BasicShapes/Cylinder.Cylinder")
        ]
        
        for part_name, part_location, part_scale, mesh_path in parts_to_create:
            part_resp = unreal.send_command("spawn_actor", {
                "name": part_name,
                "type": "StaticMeshActor",
                "location": part_location,
                "scale": part_scale,
                "static_mesh": mesh_path
            })
            if part_resp and part_resp.get("success") == True:
                body_parts.append(part_resp)
            elif part_resp and part_resp.get("success") == False and "already exists" in part_resp.get("message", ""):
                logger.info(f"Body part {part_name} already exists, skipping...")
        
        return {
            "success": True,
            "actors": body_parts,
            "mannequin_type": "primitive_humanoid",
            "message": f"Created basic humanoid figure at {location} using primitive shapes"
        }
        
    except Exception as e:
        logger.error(f"spawn_mannequin error: {e}")
        return {"success": False, "message": str(e)}

# Missing Material Color Function
@mcp.tool()
def set_mesh_material_color(
    blueprint_name: str,
    component_name: str,
    color: List[float],
    material_path: str = "/Engine/BasicShapes/BasicShapeMaterial",
    parameter_name: str = "BaseColor"
) -> Dict[str, Any]:
    """Set material color on a mesh component using the proven color system."""
    unreal = get_unreal_connection()
    if not unreal:
        return {"success": False, "message": "Failed to connect to Unreal Engine"}
    
    try:
        # Validate color format
        if not isinstance(color, list) or len(color) != 4:
            return {"success": False, "message": "Invalid color format. Must be a list of 4 float values [R, G, B, A]."}
        
        # Ensure all color values are floats between 0 and 1
        color = [float(min(1.0, max(0.0, val))) for val in color]
        
        # Set BaseColor parameter first
        params_base = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "color": color,
            "material_path": material_path,
            "parameter_name": "BaseColor"
        }
        response_base = unreal.send_command("set_mesh_material_color", params_base)
        
        # Set Color parameter second (for maximum compatibility)
        params_color = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "color": color,
            "material_path": material_path,
            "parameter_name": "Color"
        }
        response_color = unreal.send_command("set_mesh_material_color", params_color)
        
        # Return success if either parameter setting worked
        if (response_base and response_base.get("success")) or (response_color and response_color.get("success")):
            return {
                "success": True, 
                "message": f"Color applied successfully: {color}",
                "base_color_result": response_base,
                "color_result": response_color
            }
        else:
            return {
                "success": False, 
                "message": f"Failed to set color parameters. BaseColor: {response_base}, Color: {response_color}"
            }
            
    except Exception as e:
        logger.error(f"set_mesh_material_color error: {e}")
        return {"success": False, "message": str(e)}

# Advanced Town Generation System
@mcp.tool()
def create_town(
    town_size: str = "medium",  # "small", "medium", "large", "metropolis"
    building_density: float = 0.7,  # 0.0 to 1.0
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "Town",
    include_infrastructure: bool = True,
    architectural_style: str = "mixed"  # "modern", "cottage", "mansion", "mixed", "downtown", "futuristic"
) -> Dict[str, Any]:
    """Create a full dynamic town with buildings, streets, infrastructure, and vehicles."""
    try:
        import random
        random.seed()  # Use different seed each time for variety
        
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        
        logger.info(f"Creating {town_size} town with {building_density} density at {location}")
        
        # Define town parameters based on size
        town_params = {
            "small": {"blocks": 3, "block_size": 1500, "max_building_height": 5, "population": 20, "skyscraper_chance": 0.1},
            "medium": {"blocks": 5, "block_size": 2000, "max_building_height": 10, "population": 50, "skyscraper_chance": 0.3},
            "large": {"blocks": 7, "block_size": 2500, "max_building_height": 20, "population": 100, "skyscraper_chance": 0.5},
            "metropolis": {"blocks": 10, "block_size": 3000, "max_building_height": 40, "population": 200, "skyscraper_chance": 0.7}
        }
        
        params = town_params.get(town_size, town_params["medium"])
        blocks = params["blocks"]
        block_size = params["block_size"]
        max_height = params["max_building_height"]
        target_population = int(params["population"] * building_density)
        skyscraper_chance = params["skyscraper_chance"]
        
        all_spawned = []
        street_width = block_size * 0.3
        building_area = block_size * 0.7
        
        # Create street grid first
        logger.info("Creating street grid...")
        street_results = _create_street_grid(blocks, block_size, street_width, location, name_prefix)
        all_spawned.extend(street_results.get("actors", []))
        
        # Create buildings in each block
        logger.info("Placing buildings...")
        building_count = 0
        for block_x in range(blocks):
            for block_y in range(blocks):
                if building_count >= target_population:
                    break
                    
                # Skip some blocks randomly for variety
                if random.random() > building_density:
                    continue
                
                block_center_x = location[0] + (block_x - blocks/2) * block_size
                block_center_y = location[1] + (block_y - blocks/2) * block_size
                
                # Randomly choose building type based on style and location
                if architectural_style == "downtown" or architectural_style == "futuristic":
                    building_types = ["skyscraper", "office_tower", "apartment_complex", "shopping_mall", "parking_garage", "hotel"]
                elif architectural_style == "mixed":
                    # Central blocks get taller buildings
                    is_central = abs(block_x - blocks//2) <= 1 and abs(block_y - blocks//2) <= 1
                    if is_central and random.random() < skyscraper_chance:
                        building_types = ["skyscraper", "office_tower", "apartment_complex", "hotel", "shopping_mall"]
                    else:
                        building_types = ["house", "tower", "mansion", "commercial", "apartment_building", "restaurant", "store"]
                else:
                    building_types = [architectural_style] * 3 + ["commercial", "restaurant", "store"]
                
                building_type = random.choice(building_types)
                
                # Create building with variety
                building_result = _create_town_building(
                    building_type, 
                    [block_center_x, block_center_y, location[2]],
                    building_area,
                    max_height,
                    f"{name_prefix}_Building_{block_x}_{block_y}",
                    building_count
                )
                
                if building_result.get("success"):
                    all_spawned.extend(building_result.get("actors", []))
                    building_count += 1
        
        # Add infrastructure if requested
        infrastructure_count = 0
        if include_infrastructure:
            logger.info("Adding infrastructure...")
            
            # Street lights
            light_results = _create_street_lights(blocks, block_size, location, name_prefix)
            all_spawned.extend(light_results.get("actors", []))
            infrastructure_count += len(light_results.get("actors", []))
            
            # Vehicles
            vehicle_results = _create_town_vehicles(blocks, block_size, street_width, location, name_prefix, target_population // 3)
            all_spawned.extend(vehicle_results.get("actors", []))
            infrastructure_count += len(vehicle_results.get("actors", []))
            
            # Parks and decorations
            decoration_results = _create_town_decorations(blocks, block_size, location, name_prefix)
            all_spawned.extend(decoration_results.get("actors", []))
            infrastructure_count += len(decoration_results.get("actors", []))
            
            # Mannequins for population
            population_results = _create_town_population(blocks, block_size, location, name_prefix, target_population // 4)
            all_spawned.extend(population_results.get("actors", []))
            infrastructure_count += len(population_results.get("actors", []))
            
            # Add advanced infrastructure
            logger.info("Adding advanced infrastructure...")
            
            # Traffic lights at intersections
            traffic_results = _create_traffic_lights(blocks, block_size, location, name_prefix)
            all_spawned.extend(traffic_results.get("actors", []))
            infrastructure_count += len(traffic_results.get("actors", []))
            
            # Street signs and billboards
            signage_results = _create_street_signage(blocks, block_size, location, name_prefix, town_size)
            all_spawned.extend(signage_results.get("actors", []))
            infrastructure_count += len(signage_results.get("actors", []))
            
            # Sidewalks and crosswalks
            sidewalk_results = _create_sidewalks_crosswalks(blocks, block_size, street_width, location, name_prefix)
            all_spawned.extend(sidewalk_results.get("actors", []))
            infrastructure_count += len(sidewalk_results.get("actors", []))
            
            # Urban furniture (benches, trash cans, bus stops)
            furniture_results = _create_urban_furniture(blocks, block_size, location, name_prefix)
            all_spawned.extend(furniture_results.get("actors", []))
            infrastructure_count += len(furniture_results.get("actors", []))
            
            # Parking meters and hydrants
            utility_results = _create_street_utilities(blocks, block_size, location, name_prefix)
            all_spawned.extend(utility_results.get("actors", []))
            infrastructure_count += len(utility_results.get("actors", []))
            
            # Add plaza/square in center for large towns
            if town_size in ["large", "metropolis"]:
                plaza_results = _create_central_plaza(blocks, block_size, location, name_prefix)
                all_spawned.extend(plaza_results.get("actors", []))
                infrastructure_count += len(plaza_results.get("actors", []))
        
        return {
            "success": True,
            "town_stats": {
                "size": town_size,
                "density": building_density,
                "blocks": blocks,
                "buildings": building_count,
                "infrastructure_items": infrastructure_count,
                "total_actors": len(all_spawned),
                "architectural_style": architectural_style
            },
            "actors": all_spawned,
            "message": f"Created {town_size} town with {building_count} buildings and {infrastructure_count} infrastructure items"
        }
        
    except Exception as e:
        logger.error(f"create_town error: {e}")
        return {"success": False, "message": str(e)}

def _create_street_grid(blocks: int, block_size: float, street_width: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a grid of streets for the town."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        streets = []
        
        # Create horizontal streets
        for i in range(blocks + 1):
            street_y = location[1] + (i - blocks/2) * block_size
            for j in range(blocks):
                street_x = location[0] + (j - blocks/2 + 0.5) * block_size
                
                actor_name = f"{name_prefix}_Street_H_{i}_{j}"
                
                # Simple street spawn
                result = unreal.send_command("spawn_actor", {
                    "name": actor_name,
                    "type": "StaticMeshActor",
                    "location": [street_x, street_y, location[2] - 5]
                })
                
                # Scale the street segment
                if result and result.get("status") == "success":
                    set_actor_transform(
                        actor_name,
                        scale=[block_size/100.0 * 0.7, street_width/100.0, 0.1]
                    )
                    streets.append(result.get("result"))
        
        # Create vertical streets
        for i in range(blocks + 1):
            street_x = location[0] + (i - blocks/2) * block_size
            for j in range(blocks):
                street_y = location[1] + (j - blocks/2 + 0.5) * block_size
                
                actor_name = f"{name_prefix}_Street_V_{i}_{j}"
                
                # Simple street spawn
                result = unreal.send_command("spawn_actor", {
                    "name": actor_name,
                    "type": "StaticMeshActor",
                    "location": [street_x, street_y, location[2] - 5]
                })
                
                # Scale the street segment
                if result and result.get("status") == "success":
                    set_actor_transform(
                        actor_name,
                        scale=[street_width/100.0, block_size/100.0 * 0.7, 0.1]
                    )
                    streets.append(result.get("result"))
        
        return {"success": True, "actors": streets}
        
    except Exception as e:
        logger.error(f"_create_street_grid error: {e}")
        return {"success": False, "actors": []}

def _create_town_building(building_type: str, location: List[float], max_size: float, max_height: int, name_prefix: str, building_id: int) -> Dict[str, Any]:
    """Create a single building with variety."""
    try:
        import random
        
        # Add random offset within the building area
        offset_x = random.uniform(-max_size/4, max_size/4)
        offset_y = random.uniform(-max_size/4, max_size/4)
        building_loc = [location[0] + offset_x, location[1] + offset_y, location[2]]
        
        if building_type == "house":
            # Random house size and style
            styles = ["modern", "cottage"]
            width = random.randint(800, 1200)
            depth = random.randint(600, 1000)
            height = random.randint(300, 500)
            
            result = construct_house(
                width=width,
                depth=depth, 
                height=height,
                location=building_loc,
                name_prefix=f"{name_prefix}_{building_id}",
                house_style=random.choice(styles)
            )
            
        elif building_type == "mansion":
            result = construct_house(
                width=random.randint(1500, 2000),
                depth=random.randint(1200, 1600),
                height=random.randint(500, 700),
                location=building_loc,
                name_prefix=f"{name_prefix}_Mansion_{building_id}",
                house_style="mansion"
            )
            
        elif building_type == "tower":
            tower_height = random.randint(max_height//2, max_height)
            base_size = random.randint(3, 6)
            styles = ["cylindrical", "square", "tapered"]
            
            result = create_tower(
                height=tower_height,
                base_size=base_size,
                location=building_loc,
                name_prefix=f"{name_prefix}_Tower_{building_id}",
                tower_style=random.choice(styles)
            )
            
        elif building_type == "skyscraper":
            # Create impressive skyscrapers
            result = _create_skyscraper(
                height=random.randint(max(20, max_height//2), max_height),
                base_width=random.randint(600, 1000),
                base_depth=random.randint(600, 1000),
                location=building_loc,
                name_prefix=f"{name_prefix}_Skyscraper_{building_id}"
            )
            
        elif building_type == "office_tower":
            # Modern office building with glass facade
            result = _create_office_tower(
                floors=random.randint(10, max(15, max_height//2)),
                width=random.randint(800, 1200),
                depth=random.randint(800, 1200),
                location=building_loc,
                name_prefix=f"{name_prefix}_Office_{building_id}"
            )
            
        elif building_type == "apartment_complex":
            # Multi-unit residential building
            result = _create_apartment_complex(
                floors=random.randint(5, max(10, max_height//3)),
                units_per_floor=random.randint(4, 8),
                location=building_loc,
                name_prefix=f"{name_prefix}_Apartments_{building_id}"
            )
            
        elif building_type == "shopping_mall":
            # Large retail complex
            result = _create_shopping_mall(
                width=random.randint(1500, 2500),
                depth=random.randint(1500, 2500),
                floors=random.randint(2, 4),
                location=building_loc,
                name_prefix=f"{name_prefix}_Mall_{building_id}"
            )
            
        elif building_type == "parking_garage":
            # Multi-level parking structure
            result = _create_parking_garage(
                levels=random.randint(3, 6),
                width=random.randint(1000, 1500),
                depth=random.randint(800, 1200),
                location=building_loc,
                name_prefix=f"{name_prefix}_Parking_{building_id}"
            )
            
        elif building_type == "hotel":
            # Luxury hotel building
            result = _create_hotel(
                floors=random.randint(10, max(20, max_height//2)),
                width=random.randint(1000, 1500),
                depth=random.randint(800, 1200),
                location=building_loc,
                name_prefix=f"{name_prefix}_Hotel_{building_id}"
            )
            
        elif building_type == "restaurant":
            # Small restaurant/cafe
            result = _create_restaurant(
                width=random.randint(600, 1000),
                depth=random.randint(500, 800),
                location=building_loc,
                name_prefix=f"{name_prefix}_Restaurant_{building_id}"
            )
            
        elif building_type == "store":
            # Small retail store
            result = _create_store(
                width=random.randint(500, 800),
                depth=random.randint(400, 600),
                location=building_loc,
                name_prefix=f"{name_prefix}_Store_{building_id}"
            )
            
        elif building_type == "apartment_building":
            # Smaller apartment building
            result = _create_apartment_building(
                floors=random.randint(3, 5),
                width=random.randint(800, 1200),
                depth=random.randint(600, 1000),
                location=building_loc,
                name_prefix=f"{name_prefix}_AptBuilding_{building_id}"
            )
            
        else:  # commercial fallback
            # Create a simple commercial building (large rectangular)
            result = construct_house(
                width=random.randint(1000, 1500),
                depth=random.randint(800, 1200),
                height=random.randint(400, 600),
                location=building_loc,
                name_prefix=f"{name_prefix}_Commercial_{building_id}",
                house_style="modern"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"_create_town_building error: {e}")
        return {"success": False, "actors": []}

def _create_street_lights(blocks: int, block_size: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create street lights throughout the town."""
    try:
        import random
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        lights = []
        
        # Place lights at street intersections and along streets
        for i in range(blocks + 1):
            for j in range(blocks + 1):
                # Skip some randomly for variety
                if random.random() > 0.7:
                    continue
                    
                light_x = location[0] + (i - blocks/2) * block_size
                light_y = location[1] + (j - blocks/2) * block_size
                
                # Create pole (simple cylinder)
                pole_name = f"{name_prefix}_LightPole_{i}_{j}"
                pole_result = unreal.send_command("spawn_actor", {
                    "name": pole_name,
                    "type": "StaticMeshActor", 
                    "location": [light_x, light_y, location[2] + 200]
                })
                if pole_result and pole_result.get("status") == "success":
                    set_actor_transform(pole_name, scale=[0.2, 0.2, 4.0])
                    lights.append(pole_result.get("result"))
                
                # Create light (simple sphere)
                light_name = f"{name_prefix}_Light_{i}_{j}"
                light_result = unreal.send_command("spawn_actor", {
                    "name": light_name,
                    "type": "StaticMeshActor",
                    "location": [light_x, light_y, location[2] + 380]
                })
                if light_result and light_result.get("status") == "success":
                    set_actor_transform(light_name, scale=[0.3, 0.3, 0.3])
                    lights.append(light_result.get("result"))
        
        return {"success": True, "actors": lights}
        
    except Exception as e:
        logger.error(f"_create_street_lights error: {e}")
        return {"success": False, "actors": []}

def _create_town_vehicles(blocks: int, block_size: float, street_width: float, location: List[float], name_prefix: str, vehicle_count: int) -> Dict[str, Any]:
    """Create vehicles throughout the town."""
    try:
        import random
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        vehicles = []
        
        for i in range(vehicle_count):
            # Random position on streets
            street_x = location[0] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            street_y = location[1] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            
            # Create simple car (basic cube)
            car_name = f"{name_prefix}_Car_{i}"
            car_result = unreal.send_command("spawn_actor", {
                "name": car_name,
                "type": "StaticMeshActor",
                "location": [street_x, street_y, location[2] + 50]
            })
            
            if car_result and car_result.get("status") == "success":
                # Scale to car proportions
                set_actor_transform(car_name, scale=[4.0, 2.0, 1.5])
                vehicles.append(car_result.get("result"))
        
        return {"success": True, "actors": vehicles}
        
    except Exception as e:
        logger.error(f"_create_town_vehicles error: {e}")
        return {"success": False, "actors": []}

def _create_town_decorations(blocks: int, block_size: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create parks, trees, and other decorative elements."""
    try:
        import random
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        decorations = []
        
        # Create a few parks with trees
        num_parks = max(1, blocks // 3)
        for park_id in range(num_parks):
            park_x = location[0] + random.uniform(-blocks*block_size/3, blocks*block_size/3)
            park_y = location[1] + random.uniform(-blocks*block_size/3, blocks*block_size/3)
            
            # Create several trees in each park
            trees_per_park = random.randint(3, 8)
            for tree_id in range(trees_per_park):
                tree_x = park_x + random.uniform(-200, 200)
                tree_y = park_y + random.uniform(-200, 200)
                
                # Tree trunk (simple cylinder)
                trunk_name = f"{name_prefix}_TreeTrunk_{park_id}_{tree_id}"
                trunk_result = unreal.send_command("spawn_actor", {
                    "name": trunk_name,
                    "type": "StaticMeshActor",
                    "location": [tree_x, tree_y, location[2] + 150]
                })
                if trunk_result and trunk_result.get("status") == "success":
                    set_actor_transform(trunk_name, scale=[0.5, 0.5, 3.0])
                    decorations.append(trunk_result.get("result"))
                
                # Tree leaves (simple sphere)
                leaves_name = f"{name_prefix}_TreeLeaves_{park_id}_{tree_id}"
                leaves_result = unreal.send_command("spawn_actor", {
                    "name": leaves_name,
                    "type": "StaticMeshActor",
                    "location": [tree_x, tree_y, location[2] + 350]
                })
                if leaves_result and leaves_result.get("status") == "success":
                    set_actor_transform(leaves_name, scale=[2.0, 2.0, 2.0])
                    decorations.append(leaves_result.get("result"))
        
        return {"success": True, "actors": decorations}
        
    except Exception as e:
        logger.error(f"_create_town_decorations error: {e}")
        return {"success": False, "actors": []}

def _create_town_population(blocks: int, block_size: float, location: List[float], name_prefix: str, population_count: int) -> Dict[str, Any]:
    """Create mannequins to populate the town."""
    try:
        import random
        population = []
        
        mannequin_types = ["default", "manny", "quinn"]
        
        for i in range(population_count):
            # Random position throughout town
            person_x = location[0] + random.uniform(-blocks*block_size/2, blocks*block_size/2) 
            person_y = location[1] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            person_rotation = [0, 0, random.uniform(0, 360)]
            
            mannequin_type = random.choice(mannequin_types)
            
            result = spawn_mannequin(
                name=f"{name_prefix}_Person_{i}",
                location=[person_x, person_y, location[2] + 5],
                rotation=person_rotation,
                mannequin_type=mannequin_type
            )
            
            # Only add to population if successful, but continue loop either way
            if result.get("success", False):
                if "actors" in result:
                    population.extend(result["actors"])
                elif "actor" in result:
                    population.append(result["actor"])
            else:
                logger.info(f"Skipping person {i}: {result.get('message', 'Unknown error')}")
        
        return {"success": True, "actors": population}
        
    except Exception as e:
        logger.error(f"_create_town_population error: {e}")
        return {"success": False, "actors": []}

# New building creation functions for impressive structures
def _create_skyscraper(height: int, base_width: float, base_depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create an impressive skyscraper with multiple sections and details."""
    try:
        import random
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        floor_height = 150.0  # Standard floor height
        
        # Create foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 30],
            "scale": [(base_width + 200)/100.0, (base_depth + 200)/100.0, 0.6],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Create main tower in sections for tapering effect
        sections = min(5, height // 5)
        current_width = base_width
        current_depth = base_depth
        current_height = location[2]
        
        for section in range(sections):
            section_floors = height // sections
            if section == sections - 1:
                section_floors += height % sections  # Add remainder to last section
            
            # Taper the building
            taper_factor = 1 - (section * 0.1)
            current_width = base_width * max(0.6, taper_factor)
            current_depth = base_depth * max(0.6, taper_factor)
            
            # Create main structure for this section
            section_height = section_floors * floor_height
            section_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_Section_{section}",
                "type": "StaticMeshActor",
                "location": [location[0], location[1], current_height + section_height/2],
                "scale": [current_width/100.0, current_depth/100.0, section_height/100.0],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if section_result and section_result.get("status") == "success":
                actors.append(section_result.get("result"))
            
            # Add setback/balcony every few floors
            if section < sections - 1:
                balcony_result = unreal.send_command("spawn_actor", {
                    "name": f"{name_prefix}_Balcony_{section}",
                    "type": "StaticMeshActor",
                    "location": [location[0], location[1], current_height + section_height - 25],
                    "scale": [(current_width + 100)/100.0, (current_depth + 100)/100.0, 0.5],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if balcony_result and balcony_result.get("status") == "success":
                    actors.append(balcony_result.get("result"))
            
            current_height += section_height
        
        # Add rooftop features
        # Antenna/spire
        spire_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Spire",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], current_height + 300],
            "scale": [0.2, 0.2, 6.0],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if spire_result and spire_result.get("status") == "success":
            actors.append(spire_result.get("result"))
        
        # Rooftop equipment
        for i in range(3):
            equipment_x = location[0] + random.uniform(-current_width/4, current_width/4)
            equipment_y = location[1] + random.uniform(-current_depth/4, current_depth/4)
            equipment_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_RoofEquipment_{i}",
                "type": "StaticMeshActor",
                "location": [equipment_x, equipment_y, current_height + 50],
                "scale": [1.0, 1.0, 1.0],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if equipment_result and equipment_result.get("status") == "success":
                actors.append(equipment_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_skyscraper error: {e}")
        return {"success": False, "actors": []}

def _create_office_tower(floors: int, width: float, depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a modern office tower with glass facade appearance."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        floor_height = 140.0
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 15],
            "scale": [(width + 100)/100.0, (depth + 100)/100.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Lobby (taller first floor)
        lobby_height = floor_height * 1.5
        lobby_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Lobby",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + lobby_height/2],
            "scale": [width/100.0, depth/100.0, lobby_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if lobby_result and lobby_result.get("status") == "success":
            actors.append(lobby_result.get("result"))
        
        # Main tower
        tower_height = (floors - 1) * floor_height
        tower_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Tower",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + lobby_height + tower_height/2],
            "scale": [width/100.0, depth/100.0, tower_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if tower_result and tower_result.get("status") == "success":
            actors.append(tower_result.get("result"))
        
        # Add window bands every few floors for glass facade effect
        for floor in range(2, floors, 3):
            band_height = location[2] + lobby_height + (floor - 1) * floor_height
            band_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_WindowBand_{floor}",
                "type": "StaticMeshActor",
                "location": [location[0], location[1], band_height],
                "scale": [(width + 20)/100.0, (depth + 20)/100.0, 0.2],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if band_result and band_result.get("status") == "success":
                actors.append(band_result.get("result"))
        
        # Rooftop
        rooftop_height = location[2] + lobby_height + tower_height
        rooftop_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Rooftop",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], rooftop_height + 30],
            "scale": [(width - 100)/100.0, (depth - 100)/100.0, 0.6],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if rooftop_result and rooftop_result.get("status") == "success":
            actors.append(rooftop_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_office_tower error: {e}")
        return {"success": False, "actors": []}

def _create_apartment_complex(floors: int, units_per_floor: int, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a multi-unit residential complex with balconies."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        floor_height = 120.0
        width = 200 * units_per_floor // 2
        depth = 800
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 15],
            "scale": [(width + 100)/100.0, (depth + 100)/100.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Main building
        building_height = floors * floor_height
        building_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Building",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + building_height/2],
            "scale": [width/100.0, depth/100.0, building_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if building_result and building_result.get("status") == "success":
            actors.append(building_result.get("result"))
        
        # Add balconies on front and back
        for floor in range(1, floors):
            balcony_height = location[2] + floor * floor_height - 20
            
            # Front balconies
            front_balcony_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_FrontBalcony_{floor}",
                "type": "StaticMeshActor",
                "location": [location[0], location[1] - depth/2 - 50, balcony_height],
                "scale": [width/100.0, 1.0, 0.2],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if front_balcony_result and front_balcony_result.get("status") == "success":
                actors.append(front_balcony_result.get("result"))
            
            # Back balconies
            back_balcony_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_BackBalcony_{floor}",
                "type": "StaticMeshActor",
                "location": [location[0], location[1] + depth/2 + 50, balcony_height],
                "scale": [width/100.0, 1.0, 0.2],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if back_balcony_result and back_balcony_result.get("status") == "success":
                actors.append(back_balcony_result.get("result"))
        
        # Rooftop
        rooftop_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Rooftop",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + building_height + 15],
            "scale": [(width + 50)/100.0, (depth + 50)/100.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if rooftop_result and rooftop_result.get("status") == "success":
            actors.append(rooftop_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_apartment_complex error: {e}")
        return {"success": False, "actors": []}

def _create_shopping_mall(width: float, depth: float, floors: int, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a large shopping mall with entrance canopy."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        floor_height = 200.0  # Tall ceilings for retail
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 20],
            "scale": [(width + 200)/100.0, (depth + 200)/100.0, 0.4],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Main structure
        mall_height = floors * floor_height
        main_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Main",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + mall_height/2],
            "scale": [width/100.0, depth/100.0, mall_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if main_result and main_result.get("status") == "success":
            actors.append(main_result.get("result"))
        
        # Entrance canopy
        canopy_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Canopy",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2 - 150, location[2] + floor_height],
            "scale": [width/100.0 * 0.8, 3.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if canopy_result and canopy_result.get("status") == "success":
            actors.append(canopy_result.get("result"))
        
        # Entrance pillars
        for i, x_offset in enumerate([-width/3, 0, width/3]):
            pillar_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_Pillar_{i}",
                "type": "StaticMeshActor",
                "location": [location[0] + x_offset, location[1] - depth/2 - 100, location[2] + floor_height/2],
                "scale": [0.5, 0.5, floor_height/100.0],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if pillar_result and pillar_result.get("status") == "success":
                actors.append(pillar_result.get("result"))
        
        # Rooftop parking deck indicator
        parking_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_RoofParking",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + mall_height + 15],
            "scale": [width/100.0 * 0.9, depth/100.0 * 0.9, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if parking_result and parking_result.get("status") == "success":
            actors.append(parking_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_shopping_mall error: {e}")
        return {"success": False, "actors": []}

def _create_parking_garage(levels: int, width: float, depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a multi-level parking structure."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        level_height = 120.0  # Low ceiling height for parking
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 15],
            "scale": [(width + 50)/100.0, (depth + 50)/100.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Create each level with open sides
        for level in range(levels):
            level_z = location[2] + level * level_height
            
            # Floor slab
            floor_result = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_Floor_{level}",
                "type": "StaticMeshActor",
                "location": [location[0], location[1], level_z],
                "scale": [width/100.0, depth/100.0, 0.2],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if floor_result and floor_result.get("status") == "success":
                actors.append(floor_result.get("result"))
            
            # Support pillars
            for x in [-width/3, 0, width/3]:
                for y in [-depth/3, 0, depth/3]:
                    pillar_result = unreal.send_command("spawn_actor", {
                        "name": f"{name_prefix}_Pillar_{level}_{x}_{y}",
                        "type": "StaticMeshActor",
                        "location": [location[0] + x, location[1] + y, level_z + level_height/2],
                        "scale": [0.4, 0.4, level_height/100.0],
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if pillar_result and pillar_result.get("status") == "success":
                        actors.append(pillar_result.get("result"))
            
            # Side barriers (partial walls)
            if level > 0:  # Not on ground level
                for side in ["left", "right", "front", "back"]:
                    if side == "left":
                        barrier_loc = [location[0] - width/2, location[1], level_z + 40]
                        barrier_scale = [0.1, depth/100.0, 0.8]
                    elif side == "right":
                        barrier_loc = [location[0] + width/2, location[1], level_z + 40]
                        barrier_scale = [0.1, depth/100.0, 0.8]
                    elif side == "front":
                        barrier_loc = [location[0], location[1] - depth/2, level_z + 40]
                        barrier_scale = [width/100.0, 0.1, 0.8]
                    else:  # back
                        barrier_loc = [location[0], location[1] + depth/2, level_z + 40]
                        barrier_scale = [width/100.0, 0.1, 0.8]
                    
                    barrier_result = unreal.send_command("spawn_actor", {
                        "name": f"{name_prefix}_Barrier_{level}_{side}",
                        "type": "StaticMeshActor",
                        "location": barrier_loc,
                        "scale": barrier_scale,
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if barrier_result and barrier_result.get("status") == "success":
                        actors.append(barrier_result.get("result"))
        
        # Ramp structure (simplified)
        ramp_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Ramp",
            "type": "StaticMeshActor",
            "location": [location[0] + width/2 + 100, location[1], location[2] + (levels * level_height)/2],
            "scale": [1.5, 2.0, levels * level_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if ramp_result and ramp_result.get("status") == "success":
            actors.append(ramp_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_parking_garage error: {e}")
        return {"success": False, "actors": []}

def _create_hotel(floors: int, width: float, depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a luxury hotel with distinctive features."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        floor_height = 130.0
        
        # Grand foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 20],
            "scale": [(width + 150)/100.0, (depth + 150)/100.0, 0.4],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Lobby (extra tall)
        lobby_height = floor_height * 2
        lobby_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Lobby",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + lobby_height/2],
            "scale": [width/100.0, depth/100.0, lobby_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if lobby_result and lobby_result.get("status") == "success":
            actors.append(lobby_result.get("result"))
        
        # Main tower
        tower_height = (floors - 2) * floor_height
        tower_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Tower",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + lobby_height + tower_height/2],
            "scale": [width/100.0 * 0.9, depth/100.0 * 0.9, tower_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if tower_result and tower_result.get("status") == "success":
            actors.append(tower_result.get("result"))
        
        # Penthouse (top floor wider)
        penthouse_height = location[2] + lobby_height + tower_height
        penthouse_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Penthouse",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], penthouse_height + floor_height/2],
            "scale": [width/100.0, depth/100.0, floor_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if penthouse_result and penthouse_result.get("status") == "success":
            actors.append(penthouse_result.get("result"))
        
        # Rooftop pool area
        pool_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Pool",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], penthouse_height + floor_height + 20],
            "scale": [width/100.0 * 0.5, depth/100.0 * 0.3, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if pool_result and pool_result.get("status") == "success":
            actors.append(pool_result.get("result"))
        
        # Entrance canopy
        canopy_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Canopy",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2 - 100, location[2] + 150],
            "scale": [width/100.0 * 0.6, 2.0, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if canopy_result and canopy_result.get("status") == "success":
            actors.append(canopy_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_hotel error: {e}")
        return {"success": False, "actors": []}

def _create_restaurant(width: float, depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a small restaurant/cafe building."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        height = 150.0
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 10],
            "scale": [(width + 50)/100.0, (depth + 50)/100.0, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Main building
        main_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Main",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + height/2],
            "scale": [width/100.0, depth/100.0, height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if main_result and main_result.get("status") == "success":
            actors.append(main_result.get("result"))
        
        # Outdoor seating area (patio)
        patio_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Patio",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2 - 75, location[2]],
            "scale": [width/100.0, 1.5, 0.1],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if patio_result and patio_result.get("status") == "success":
            actors.append(patio_result.get("result"))
        
        # Awning
        awning_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Awning",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2 - 50, location[2] + height - 20],
            "scale": [width/100.0 * 1.2, 1.0, 0.1],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if awning_result and awning_result.get("status") == "success":
            actors.append(awning_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_restaurant error: {e}")
        return {"success": False, "actors": []}

def _create_store(width: float, depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a small retail store."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        height = 140.0
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 10],
            "scale": [(width + 30)/100.0, (depth + 30)/100.0, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Main building
        main_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Main",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + height/2],
            "scale": [width/100.0, depth/100.0, height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if main_result and main_result.get("status") == "success":
            actors.append(main_result.get("result"))
        
        # Storefront sign
        sign_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Sign",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2 - 10, location[2] + height + 20],
            "scale": [width/100.0 * 0.8, 0.1, 0.4],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if sign_result and sign_result.get("status") == "success":
            actors.append(sign_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_store error: {e}")
        return {"success": False, "actors": []}

def _create_apartment_building(floors: int, width: float, depth: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a smaller residential apartment building."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        actors = []
        floor_height = 110.0
        
        # Foundation
        foundation_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Foundation",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] - 15],
            "scale": [(width + 50)/100.0, (depth + 50)/100.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if foundation_result and foundation_result.get("status") == "success":
            actors.append(foundation_result.get("result"))
        
        # Main building
        building_height = floors * floor_height
        building_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Building",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + building_height/2],
            "scale": [width/100.0, depth/100.0, building_height/100.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if building_result and building_result.get("status") == "success":
            actors.append(building_result.get("result"))
        
        # Entry steps
        steps_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Steps",
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - depth/2 - 30, location[2] + 10],
            "scale": [width/100.0 * 0.3, 0.6, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if steps_result and steps_result.get("status") == "success":
            actors.append(steps_result.get("result"))
        
        # Simple roof
        roof_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Roof",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + building_height + 15],
            "scale": [(width + 20)/100.0, (depth + 20)/100.0, 0.3],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if roof_result and roof_result.get("status") == "success":
            actors.append(roof_result.get("result"))
        
        return {"success": True, "actors": actors}
        
    except Exception as e:
        logger.error(f"_create_apartment_building error: {e}")
        return {"success": False, "actors": []}

# Infrastructure creation functions
def _create_traffic_lights(blocks: int, block_size: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create traffic lights at major intersections."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        import random
        traffic_lights = []
        
        # Place traffic lights at major intersections
        for i in range(1, blocks, 2):  # Every other intersection
            for j in range(1, blocks, 2):
                intersection_x = location[0] + (i - blocks/2) * block_size
                intersection_y = location[1] + (j - blocks/2) * block_size
                
                # Create traffic light poles at four corners
                for corner in range(4):
                    angle = corner * math.pi / 2
                    offset = 150  # Distance from intersection center
                    
                    pole_x = intersection_x + offset * math.cos(angle)
                    pole_y = intersection_y + offset * math.sin(angle)
                    
                    # Pole
                    pole_name = f"{name_prefix}_TrafficPole_{i}_{j}_{corner}"
                    pole_result = unreal.send_command("spawn_actor", {
                        "name": pole_name,
                        "type": "StaticMeshActor",
                        "location": [pole_x, pole_y, location[2] + 150],
                        "scale": [0.15, 0.15, 3.0],
                        "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                    })
                    if pole_result and pole_result.get("status") == "success":
                        traffic_lights.append(pole_result.get("result"))
                    
                    # Traffic light box
                    light_name = f"{name_prefix}_TrafficLight_{i}_{j}_{corner}"
                    light_result = unreal.send_command("spawn_actor", {
                        "name": light_name,
                        "type": "StaticMeshActor",
                        "location": [pole_x, pole_y, location[2] + 280],
                        "scale": [0.3, 0.2, 0.8],
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if light_result and light_result.get("status") == "success":
                        traffic_lights.append(light_result.get("result"))
        
        return {"success": True, "actors": traffic_lights}
        
    except Exception as e:
        logger.error(f"_create_traffic_lights error: {e}")
        return {"success": False, "actors": []}

def _create_street_signage(blocks: int, block_size: float, location: List[float], name_prefix: str, town_size: str) -> Dict[str, Any]:
    """Create street signs and billboards."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        import random
        signage = []
        
        # Street name signs at corners
        street_names = ["Main St", "1st Ave", "2nd Ave", "Park Blvd", "Commerce Dr", "Tech Way"]
        
        for i in range(0, blocks + 1, 2):
            for j in range(0, blocks + 1, 2):
                if random.random() > 0.5:
                    continue
                    
                sign_x = location[0] + (i - blocks/2) * block_size + 100
                sign_y = location[1] + (j - blocks/2) * block_size + 100
                
                # Sign pole
                pole_name = f"{name_prefix}_SignPole_{i}_{j}"
                pole_result = unreal.send_command("spawn_actor", {
                    "name": pole_name,
                    "type": "StaticMeshActor",
                    "location": [sign_x, sign_y, location[2] + 100],
                    "scale": [0.1, 0.1, 2.0],
                    "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                })
                if pole_result and pole_result.get("status") == "success":
                    signage.append(pole_result.get("result"))
                
                # Sign
                sign_name = f"{name_prefix}_StreetSign_{i}_{j}"
                sign_result = unreal.send_command("spawn_actor", {
                    "name": sign_name,
                    "type": "StaticMeshActor",
                    "location": [sign_x, sign_y, location[2] + 180],
                    "scale": [1.5, 0.05, 0.3],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if sign_result and sign_result.get("status") == "success":
                    signage.append(sign_result.get("result"))
        
        # Billboards for larger towns
        if town_size in ["large", "metropolis"]:
            num_billboards = random.randint(3, 8)
            for b in range(num_billboards):
                billboard_x = location[0] + random.uniform(-blocks*block_size/3, blocks*block_size/3)
                billboard_y = location[1] + random.uniform(-blocks*block_size/3, blocks*block_size/3)
                
                # Billboard structure
                billboard_name = f"{name_prefix}_Billboard_{b}"
                billboard_result = unreal.send_command("spawn_actor", {
                    "name": billboard_name,
                    "type": "StaticMeshActor",
                    "location": [billboard_x, billboard_y, location[2] + 400],
                    "scale": [3.0, 0.1, 2.0],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if billboard_result and billboard_result.get("status") == "success":
                    signage.append(billboard_result.get("result"))
                
                # Billboard supports
                for support_offset in [-100, 100]:
                    support_name = f"{name_prefix}_BillboardSupport_{b}_{support_offset}"
                    support_result = unreal.send_command("spawn_actor", {
                        "name": support_name,
                        "type": "StaticMeshActor",
                        "location": [billboard_x + support_offset, billboard_y, location[2] + 200],
                        "scale": [0.2, 0.2, 4.0],
                        "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                    })
                    if support_result and support_result.get("status") == "success":
                        signage.append(support_result.get("result"))
        
        return {"success": True, "actors": signage}
        
    except Exception as e:
        logger.error(f"_create_street_signage error: {e}")
        return {"success": False, "actors": []}

def _create_sidewalks_crosswalks(blocks: int, block_size: float, street_width: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create sidewalks and crosswalks."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        sidewalks = []
        sidewalk_width = 150.0
        
        # Create sidewalks along streets
        for i in range(blocks):
            for j in range(blocks + 1):
                # Horizontal sidewalks
                sidewalk_y = location[1] + (j - blocks/2) * block_size
                sidewalk_x = location[0] + (i - blocks/2 + 0.5) * block_size
                
                # North sidewalk
                north_sidewalk_result = unreal.send_command("spawn_actor", {
                    "name": f"{name_prefix}_SidewalkH_North_{i}_{j}",
                    "type": "StaticMeshActor",
                    "location": [sidewalk_x, sidewalk_y - street_width/2 + sidewalk_width/2, location[2]],
                    "scale": [block_size/100.0 * 0.7, sidewalk_width/100.0, 0.05],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if north_sidewalk_result and north_sidewalk_result.get("status") == "success":
                    sidewalks.append(north_sidewalk_result.get("result"))
                
                # South sidewalk
                south_sidewalk_result = unreal.send_command("spawn_actor", {
                    "name": f"{name_prefix}_SidewalkH_South_{i}_{j}",
                    "type": "StaticMeshActor",
                    "location": [sidewalk_x, sidewalk_y + street_width/2 - sidewalk_width/2, location[2]],
                    "scale": [block_size/100.0 * 0.7, sidewalk_width/100.0, 0.05],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if south_sidewalk_result and south_sidewalk_result.get("status") == "success":
                    sidewalks.append(south_sidewalk_result.get("result"))
        
        # Vertical sidewalks
        for i in range(blocks + 1):
            for j in range(blocks):
                sidewalk_x = location[0] + (i - blocks/2) * block_size
                sidewalk_y = location[1] + (j - blocks/2 + 0.5) * block_size
                
                # East sidewalk
                east_sidewalk_result = unreal.send_command("spawn_actor", {
                    "name": f"{name_prefix}_SidewalkV_East_{i}_{j}",
                    "type": "StaticMeshActor",
                    "location": [sidewalk_x - street_width/2 + sidewalk_width/2, sidewalk_y, location[2]],
                    "scale": [sidewalk_width/100.0, block_size/100.0 * 0.7, 0.05],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if east_sidewalk_result and east_sidewalk_result.get("status") == "success":
                    sidewalks.append(east_sidewalk_result.get("result"))
                
                # West sidewalk
                west_sidewalk_result = unreal.send_command("spawn_actor", {
                    "name": f"{name_prefix}_SidewalkV_West_{i}_{j}",
                    "type": "StaticMeshActor",
                    "location": [sidewalk_x + street_width/2 - sidewalk_width/2, sidewalk_y, location[2]],
                    "scale": [sidewalk_width/100.0, block_size/100.0 * 0.7, 0.05],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if west_sidewalk_result and west_sidewalk_result.get("status") == "success":
                    sidewalks.append(west_sidewalk_result.get("result"))
        
        # Create crosswalks at intersections
        crosswalk_width = 200.0
        for i in range(blocks + 1):
            for j in range(blocks + 1):
                intersection_x = location[0] + (i - blocks/2) * block_size
                intersection_y = location[1] + (j - blocks/2) * block_size
                
                # Create crosswalk stripes
                for stripe in range(5):
                    stripe_offset = (stripe - 2) * 40
                    
                    # North-South crosswalk
                    ns_crosswalk_result = unreal.send_command("spawn_actor", {
                        "name": f"{name_prefix}_CrosswalkNS_{i}_{j}_{stripe}",
                        "type": "StaticMeshActor",
                        "location": [intersection_x + stripe_offset, intersection_y, location[2] + 1],
                        "scale": [0.3, crosswalk_width/100.0, 0.02],
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if ns_crosswalk_result and ns_crosswalk_result.get("status") == "success":
                        sidewalks.append(ns_crosswalk_result.get("result"))
                    
                    # East-West crosswalk
                    ew_crosswalk_result = unreal.send_command("spawn_actor", {
                        "name": f"{name_prefix}_CrosswalkEW_{i}_{j}_{stripe}",
                        "type": "StaticMeshActor",
                        "location": [intersection_x, intersection_y + stripe_offset, location[2] + 1],
                        "scale": [crosswalk_width/100.0, 0.3, 0.02],
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if ew_crosswalk_result and ew_crosswalk_result.get("status") == "success":
                        sidewalks.append(ew_crosswalk_result.get("result"))
        
        return {"success": True, "actors": sidewalks}
        
    except Exception as e:
        logger.error(f"_create_sidewalks_crosswalks error: {e}")
        return {"success": False, "actors": []}

def _create_urban_furniture(blocks: int, block_size: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create benches, trash cans, and bus stops."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        import random
        furniture = []
        
        # Place furniture along sidewalks
        num_furniture_items = blocks * blocks // 2
        
        for f in range(num_furniture_items):
            # Random position along a street
            street_x = location[0] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            street_y = location[1] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            
            # Offset to sidewalk
            sidewalk_offset = random.choice([-200, 200])
            if random.random() > 0.5:
                furniture_x = street_x + sidewalk_offset
                furniture_y = street_y
            else:
                furniture_x = street_x
                furniture_y = street_y + sidewalk_offset
            
            furniture_type = random.choice(["bench", "trash", "bus_stop"])
            
            if furniture_type == "bench":
                # Create bench
                bench_name = f"{name_prefix}_Bench_{f}"
                bench_result = unreal.send_command("spawn_actor", {
                    "name": bench_name,
                    "type": "StaticMeshActor",
                    "location": [furniture_x, furniture_y, location[2] + 30],
                    "scale": [1.5, 0.5, 0.6],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if bench_result and bench_result.get("status") == "success":
                    furniture.append(bench_result.get("result"))
                
                # Bench supports
                for support_offset in [-50, 50]:
                    support_name = f"{name_prefix}_BenchSupport_{f}_{support_offset}"
                    support_result = unreal.send_command("spawn_actor", {
                        "name": support_name,
                        "type": "StaticMeshActor",
                        "location": [furniture_x + support_offset, furniture_y, location[2] + 15],
                        "scale": [0.1, 0.5, 0.3],
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if support_result and support_result.get("status") == "success":
                        furniture.append(support_result.get("result"))
            
            elif furniture_type == "trash":
                # Create trash can
                trash_name = f"{name_prefix}_TrashCan_{f}"
                trash_result = unreal.send_command("spawn_actor", {
                    "name": trash_name,
                    "type": "StaticMeshActor",
                    "location": [furniture_x, furniture_y, location[2] + 40],
                    "scale": [0.4, 0.4, 0.8],
                    "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                })
                if trash_result and trash_result.get("status") == "success":
                    furniture.append(trash_result.get("result"))
            
            else:  # bus_stop
                # Create bus stop shelter
                shelter_name = f"{name_prefix}_BusStop_{f}"
                shelter_result = unreal.send_command("spawn_actor", {
                    "name": shelter_name,
                    "type": "StaticMeshActor",
                    "location": [furniture_x, furniture_y, location[2] + 120],
                    "scale": [2.0, 1.0, 0.1],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if shelter_result and shelter_result.get("status") == "success":
                    furniture.append(shelter_result.get("result"))
                
                # Bus stop posts
                for post_x in [-80, 80]:
                    post_name = f"{name_prefix}_BusStopPost_{f}_{post_x}"
                    post_result = unreal.send_command("spawn_actor", {
                        "name": post_name,
                        "type": "StaticMeshActor",
                        "location": [furniture_x + post_x, furniture_y, location[2] + 60],
                        "scale": [0.1, 0.1, 1.2],
                        "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                    })
                    if post_result and post_result.get("status") == "success":
                        furniture.append(post_result.get("result"))
                
                # Bus stop bench
                bench_name = f"{name_prefix}_BusStopBench_{f}"
                bench_result = unreal.send_command("spawn_actor", {
                    "name": bench_name,
                    "type": "StaticMeshActor",
                    "location": [furniture_x, furniture_y + 30, location[2] + 25],
                    "scale": [1.8, 0.4, 0.5],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if bench_result and bench_result.get("status") == "success":
                    furniture.append(bench_result.get("result"))
        
        return {"success": True, "actors": furniture}
        
    except Exception as e:
        logger.error(f"_create_urban_furniture error: {e}")
        return {"success": False, "actors": []}

def _create_street_utilities(blocks: int, block_size: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create parking meters and fire hydrants."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        import random
        utilities = []
        
        # Parking meters along commercial streets
        num_meters = blocks * 4
        for m in range(num_meters):
            meter_x = location[0] + random.uniform(-blocks*block_size/3, blocks*block_size/3)
            meter_y = location[1] + random.uniform(-blocks*block_size/3, blocks*block_size/3)
            
            # Place on sidewalk edge
            sidewalk_offset = random.choice([-180, 180])
            if random.random() > 0.5:
                meter_x += sidewalk_offset
            else:
                meter_y += sidewalk_offset
            
            # Parking meter
            meter_name = f"{name_prefix}_ParkingMeter_{m}"
            meter_result = unreal.send_command("spawn_actor", {
                "name": meter_name,
                "type": "StaticMeshActor",
                "location": [meter_x, meter_y, location[2] + 50],
                "scale": [0.15, 0.15, 1.0],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if meter_result and meter_result.get("status") == "success":
                utilities.append(meter_result.get("result"))
            
            # Meter head
            head_name = f"{name_prefix}_MeterHead_{m}"
            head_result = unreal.send_command("spawn_actor", {
                "name": head_name,
                "type": "StaticMeshActor",
                "location": [meter_x, meter_y, location[2] + 100],
                "scale": [0.25, 0.15, 0.3],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if head_result and head_result.get("status") == "success":
                utilities.append(head_result.get("result"))
        
        # Fire hydrants at corners
        num_hydrants = blocks + 2
        for h in range(num_hydrants):
            hydrant_x = location[0] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            hydrant_y = location[1] + random.uniform(-blocks*block_size/2, blocks*block_size/2)
            
            # Fire hydrant
            hydrant_name = f"{name_prefix}_Hydrant_{h}"
            hydrant_result = unreal.send_command("spawn_actor", {
                "name": hydrant_name,
                "type": "StaticMeshActor",
                "location": [hydrant_x, hydrant_y, location[2] + 40],
                "scale": [0.3, 0.3, 0.8],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if hydrant_result and hydrant_result.get("status") == "success":
                utilities.append(hydrant_result.get("result"))
            
            # Hydrant cap
            cap_name = f"{name_prefix}_HydrantCap_{h}"
            cap_result = unreal.send_command("spawn_actor", {
                "name": cap_name,
                "type": "StaticMeshActor",
                "location": [hydrant_x, hydrant_y, location[2] + 75],
                "scale": [0.35, 0.35, 0.1],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if cap_result and cap_result.get("status") == "success":
                utilities.append(cap_result.get("result"))
        
        return {"success": True, "actors": utilities}
        
    except Exception as e:
        logger.error(f"_create_street_utilities error: {e}")
        return {"success": False, "actors": []}

def _create_central_plaza(blocks: int, block_size: float, location: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create a central plaza with fountain and monuments."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "actors": []}
            
        plaza = []
        plaza_size = block_size * 0.8
        
        # Plaza floor
        plaza_floor_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_PlazaFloor",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + 2],
            "scale": [plaza_size/100.0, plaza_size/100.0, 0.05],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if plaza_floor_result and plaza_floor_result.get("status") == "success":
            plaza.append(plaza_floor_result.get("result"))
        
        # Central fountain base
        fountain_base_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_FountainBase",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + 10],
            "scale": [3.0, 3.0, 0.2],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if fountain_base_result and fountain_base_result.get("status") == "success":
            plaza.append(fountain_base_result.get("result"))
        
        # Fountain center
        fountain_center_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_FountainCenter",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + 50],
            "scale": [0.5, 0.5, 0.8],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if fountain_center_result and fountain_center_result.get("status") == "success":
            plaza.append(fountain_center_result.get("result"))
        
        # Fountain top
        fountain_top_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_FountainTop",
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + 80],
            "scale": [1.5, 1.5, 0.1],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if fountain_top_result and fountain_top_result.get("status") == "success":
            plaza.append(fountain_top_result.get("result"))
        
        # Monument/statue
        monument_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_Monument",
            "type": "StaticMeshActor",
            "location": [location[0] + plaza_size/3, location[1], location[2] + 100],
            "scale": [1.0, 1.0, 2.0],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if monument_result and monument_result.get("status") == "success":
            plaza.append(monument_result.get("result"))
        
        # Monument base
        monument_base_result = unreal.send_command("spawn_actor", {
            "name": f"{name_prefix}_MonumentBase",
            "type": "StaticMeshActor",
            "location": [location[0] + plaza_size/3, location[1], location[2] + 30],
            "scale": [2.0, 2.0, 0.6],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if monument_base_result and monument_base_result.get("status") == "success":
            plaza.append(monument_base_result.get("result"))
        
        # Plaza benches in circle
        num_benches = 8
        for i in range(num_benches):
            angle = (2 * math.pi * i) / num_benches
            bench_x = location[0] + plaza_size/3 * math.cos(angle)
            bench_y = location[1] + plaza_size/3 * math.sin(angle)
            bench_rotation = [0, 0, angle * 180/math.pi]
            
            bench_name = f"{name_prefix}_PlazaBench_{i}"
            bench_result = unreal.send_command("spawn_actor", {
                "name": bench_name,
                "type": "StaticMeshActor",
                "location": [bench_x, bench_y, location[2] + 30],
                "rotation": bench_rotation,
                "scale": [1.5, 0.5, 0.6],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if bench_result and bench_result.get("status") == "success":
                plaza.append(bench_result.get("result"))
        
        # Decorative light posts around plaza
        num_lights = 12
        for i in range(num_lights):
            angle = (2 * math.pi * i) / num_lights
            light_x = location[0] + plaza_size/2 * math.cos(angle)
            light_y = location[1] + plaza_size/2 * math.sin(angle)
            
            # Decorative light post
            post_name = f"{name_prefix}_PlazaLightPost_{i}"
            post_result = unreal.send_command("spawn_actor", {
                "name": post_name,
                "type": "StaticMeshActor",
                "location": [light_x, light_y, location[2] + 100],
                "scale": [0.15, 0.15, 2.0],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if post_result and post_result.get("status") == "success":
                plaza.append(post_result.get("result"))
            
            # Light fixture
            light_name = f"{name_prefix}_PlazaLight_{i}"
            light_result = unreal.send_command("spawn_actor", {
                "name": light_name,
                "type": "StaticMeshActor",
                "location": [light_x, light_y, location[2] + 180],
                "scale": [0.4, 0.4, 0.3],
                "static_mesh": "/Engine/BasicShapes/Sphere.Sphere"
            })
            if light_result and light_result.get("status") == "success":
                plaza.append(light_result.get("result"))
        
        return {"success": True, "actors": plaza}
        
    except Exception as e:
        logger.error(f"_create_central_plaza error: {e}")
        return {"success": False, "actors": []}

@mcp.tool()
def create_castle_fortress(
    castle_size: str = "large",  # "small", "medium", "large", "epic"
    location: List[float] = [0.0, 0.0, 0.0],
    name_prefix: str = "Castle",
    include_siege_weapons: bool = True,
    include_village: bool = True,
    architectural_style: str = "medieval"  # "medieval", "fantasy", "gothic"
) -> Dict[str, Any]:
    """
    Create a massive castle fortress with walls, towers, courtyards, throne room,
    dungeons, and surrounding village. Perfect for dramatic TikTok reveals showing
    the scale and detail of a complete medieval fortress.
    """
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        
        logger.info(f"Creating {castle_size} {architectural_style} castle fortress")
        all_actors = []
        
        # Define castle dimensions based on size - MUCH BIGGER AND MORE COMPLEX
        size_params = {
            "small": {"outer_width": 6000, "outer_depth": 6000, "inner_width": 3000, "inner_depth": 3000, "wall_height": 800, "tower_count": 8, "tower_height": 1200},
            "medium": {"outer_width": 8000, "outer_depth": 8000, "inner_width": 4000, "inner_depth": 4000, "wall_height": 1000, "tower_count": 12, "tower_height": 1600},
            "large": {"outer_width": 12000, "outer_depth": 12000, "inner_width": 6000, "inner_depth": 6000, "wall_height": 1200, "tower_count": 16, "tower_height": 2000},
            "epic": {"outer_width": 16000, "outer_depth": 16000, "inner_width": 8000, "inner_depth": 8000, "wall_height": 1600, "tower_count": 24, "tower_height": 2800}
        }
        
        params = size_params.get(castle_size, size_params["large"])
        # Global scale/complexity multipliers applied across ALL styles and sizes
        # This makes every variant ~4x larger and adds denser details everywhere.
        scale_factor: float = 2.0
        complexity_multiplier: int = max(1, int(round(scale_factor)))

        outer_width = int(params["outer_width"] * scale_factor)
        outer_depth = int(params["outer_depth"] * scale_factor)
        inner_width = int(params["inner_width"] * scale_factor)
        inner_depth = int(params["inner_depth"] * scale_factor)
        wall_height = int(params["wall_height"] * scale_factor)
        tower_count = int(params["tower_count"] * complexity_multiplier)
        tower_height = int(params["tower_height"] * scale_factor)

        # Frequently reused scaled offsets
        gate_tower_offset = int(700 * scale_factor)
        barbican_offset = int(400 * scale_factor)
        drawbridge_offset = int(600 * scale_factor)
        
        # MASSIVE COMPLEX CASTLE - BUILD OUTER BAILEY WALLS FIRST
        logger.info("Constructing massive outer bailey walls...")
        wall_thickness = int(300 * max(1.0, scale_factor * 0.75))
        
        # OUTER BAILEY - North wall
        for i in range(int(outer_width / 200)):
            wall_x = location[0] - outer_width/2 + i * 200 + 100
            wall_name = f"{name_prefix}_WallNorth_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [wall_x, location[1] - outer_depth/2, location[2] + wall_height/2],
                "scale": [2.0, wall_thickness/100, wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
            
            # Dense battlements
            if i % 2 == 0:
                battlement_name = f"{name_prefix}_BattlementNorth_{i}"
                battlement_result = unreal.send_command("spawn_actor", {
                    "name": battlement_name,
                    "type": "StaticMeshActor",
                    "location": [wall_x, location[1] - outer_depth/2, location[2] + wall_height + 50],
                    "scale": [1.0, wall_thickness/100, 1.0],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if battlement_result and battlement_result.get("status") == "success":
                    all_actors.append(battlement_result.get("result"))
        
        # OUTER BAILEY - South wall
        for i in range(int(outer_width / 200)):
            wall_x = location[0] - outer_width/2 + i * 200 + 100
            wall_name = f"{name_prefix}_WallSouth_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [wall_x, location[1] + outer_depth/2, location[2] + wall_height/2],
                "scale": [2.0, wall_thickness/100, wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
            
            if i % 2 == 0:
                battlement_name = f"{name_prefix}_BattlementSouth_{i}"
                battlement_result = unreal.send_command("spawn_actor", {
                    "name": battlement_name,
                    "type": "StaticMeshActor",
                    "location": [wall_x, location[1] + outer_depth/2, location[2] + wall_height + 50],
                    "scale": [1.0, wall_thickness/100, 1.0],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if battlement_result and battlement_result.get("status") == "success":
                    all_actors.append(battlement_result.get("result"))
        
        # OUTER BAILEY - East wall
        for i in range(int(outer_depth / 200)):
            wall_y = location[1] - outer_depth/2 + i * 200 + 100
            wall_name = f"{name_prefix}_WallEast_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [location[0] + outer_width/2, wall_y, location[2] + wall_height/2],
                "scale": [wall_thickness/100, 2.0, wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
        
        # OUTER BAILEY - West wall with main gate (much more elaborate)
        for i in range(int(outer_depth / 200)):
            wall_y = location[1] - outer_depth/2 + i * 200 + 100
            # Skip middle sections for massive gate
            if abs(wall_y - location[1]) > 700:
                wall_name = f"{name_prefix}_WallWest_{i}"
                wall_result = unreal.send_command("spawn_actor", {
                    "name": wall_name,
                    "type": "StaticMeshActor",
                    "location": [location[0] - outer_width/2, wall_y, location[2] + wall_height/2],
                    "scale": [wall_thickness/100, 2.0, wall_height/100],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if wall_result and wall_result.get("status") == "success":
                    all_actors.append(wall_result.get("result"))
        
        # BUILD INNER BAILEY WALLS (HIGHER AND STRONGER)
        logger.info("Building inner bailey fortifications...")
        inner_wall_height = wall_height * 1.3
        
        # Inner North wall
        for i in range(int(inner_width / 200)):
            wall_x = location[0] - inner_width/2 + i * 200 + 100
            wall_name = f"{name_prefix}_InnerWallNorth_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [wall_x, location[1] - inner_depth/2, location[2] + inner_wall_height/2],
                "scale": [2.0, wall_thickness/100, inner_wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
        
        # Inner South wall  
        for i in range(int(inner_width / 200)):
            wall_x = location[0] - inner_width/2 + i * 200 + 100
            wall_name = f"{name_prefix}_InnerWallSouth_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [wall_x, location[1] + inner_depth/2, location[2] + inner_wall_height/2],
                "scale": [2.0, wall_thickness/100, inner_wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
        
        # Inner East and West walls
        for i in range(int(inner_depth / 200)):
            wall_y = location[1] - inner_depth/2 + i * 200 + 100
            
            # East inner wall
            wall_name = f"{name_prefix}_InnerWallEast_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [location[0] + inner_width/2, wall_y, location[2] + inner_wall_height/2],
                "scale": [wall_thickness/100, 2.0, inner_wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
            
            # West inner wall
            wall_name = f"{name_prefix}_InnerWallWest_{i}"
            wall_result = unreal.send_command("spawn_actor", {
                "name": wall_name,
                "type": "StaticMeshActor",
                "location": [location[0] - inner_width/2, wall_y, location[2] + inner_wall_height/2],
                "scale": [wall_thickness/100, 2.0, inner_wall_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if wall_result and wall_result.get("status") == "success":
                all_actors.append(wall_result.get("result"))
        
        # Build MASSIVE main gate complex
        logger.info("Building elaborate main gate complex...")
        
        # OUTER Gate towers (much larger)
        for side in [-1, 1]:
            gate_tower_name = f"{name_prefix}_GateTower_{side}"
            gate_tower_result = unreal.send_command("spawn_actor", {
                "name": gate_tower_name,
                "type": "StaticMeshActor",
                "location": [
                    location[0] - outer_width/2,
                    location[1] + side * gate_tower_offset,
                    location[2] + tower_height/2
                ],
                "scale": [4.0, 4.0, tower_height/100],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if gate_tower_result and gate_tower_result.get("status") == "success":
                all_actors.append(gate_tower_result.get("result"))
            
            # Massive tower tops
            tower_top_name = f"{name_prefix}_GateTowerTop_{side}"
            tower_top_result = unreal.send_command("spawn_actor", {
                "name": tower_top_name,
                "type": "StaticMeshActor",
                "location": [
                    location[0] - outer_width/2,
                    location[1] + side * gate_tower_offset,
                    location[2] + tower_height + 200
                ],
                "scale": [5.0, 5.0, 0.8],
                "static_mesh": "/Engine/BasicShapes/Cone.Cone"
            })
            if tower_top_result and tower_top_result.get("status") == "success":
                all_actors.append(tower_top_result.get("result"))
        
        # BARBICAN (outer gate structure) 
        barbican_name = f"{name_prefix}_Barbican"
        barbican_result = unreal.send_command("spawn_actor", {
            "name": barbican_name,
            "type": "StaticMeshActor",
            "location": [location[0] - outer_width/2 - barbican_offset, location[1], location[2] + wall_height/2],
            "scale": [8.0, 12.0, wall_height/100],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if barbican_result and barbican_result.get("status") == "success":
            all_actors.append(barbican_result.get("result"))
        
        # Main Portcullis (gate)
        portcullis_name = f"{name_prefix}_Portcullis"
        portcullis_result = unreal.send_command("spawn_actor", {
            "name": portcullis_name,
            "type": "StaticMeshActor",
            "location": [location[0] - outer_width/2, location[1], location[2] + 200],
            "scale": [0.5, 12.0, 8.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if portcullis_result and portcullis_result.get("status") == "success":
            all_actors.append(portcullis_result.get("result"))
        
        # Inner gate for inner bailey
        inner_portcullis_name = f"{name_prefix}_InnerPortcullis"
        inner_portcullis_result = unreal.send_command("spawn_actor", {
            "name": inner_portcullis_name,
            "type": "StaticMeshActor",
            "location": [location[0] - inner_width/2, location[1], location[2] + 200],
            "scale": [0.5, 8.0, 6.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if inner_portcullis_result and inner_portcullis_result.get("status") == "success":
            all_actors.append(inner_portcullis_result.get("result"))
        
        # Build MASSIVE corner towers - OUTER BAILEY
        logger.info("Constructing massive corner towers...")
        outer_corners = [
            [location[0] - outer_width/2, location[1] - outer_depth/2],  # NW
            [location[0] + outer_width/2, location[1] - outer_depth/2],  # NE
            [location[0] + outer_width/2, location[1] + outer_depth/2],  # SE
            [location[0] - outer_width/2, location[1] + outer_depth/2],  # SW
        ]
        
        # INNER BAILEY corner towers (even bigger)
        inner_corners = [
            [location[0] - inner_width/2, location[1] - inner_depth/2],  # NW
            [location[0] + inner_width/2, location[1] - inner_depth/2],  # NE
            [location[0] + inner_width/2, location[1] + inner_depth/2],  # SE
            [location[0] - inner_width/2, location[1] + inner_depth/2],  # SW
        ]
        
        # Build MASSIVE outer bailey corner towers
        for i, corner in enumerate(outer_corners):
            # HUGE Tower base (much wider)
            tower_base_name = f"{name_prefix}_TowerBase_{i}"
            tower_base_result = unreal.send_command("spawn_actor", {
                "name": tower_base_name,
                "type": "StaticMeshActor",
                "location": [corner[0], corner[1], location[2] + 150],
                "scale": [6.0, 6.0, 3.0],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if tower_base_result and tower_base_result.get("status") == "success":
                all_actors.append(tower_base_result.get("result"))
            
            # MASSIVE Main tower
            tower_name = f"{name_prefix}_Tower_{i}"
            tower_result = unreal.send_command("spawn_actor", {
                "name": tower_name,
                "type": "StaticMeshActor",
                "location": [corner[0], corner[1], location[2] + tower_height/2],
                "scale": [5.0, 5.0, tower_height/100],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if tower_result and tower_result.get("status") == "success":
                all_actors.append(tower_result.get("result"))
            
            # HUGE Tower top (cone roof)
            if architectural_style in ["medieval", "fantasy"]:
                tower_top_name = f"{name_prefix}_TowerTop_{i}"
                tower_top_result = unreal.send_command("spawn_actor", {
                    "name": tower_top_name,
                    "type": "StaticMeshActor",
                    "location": [corner[0], corner[1], location[2] + tower_height + 150],
                    "scale": [6.0, 6.0, 2.5],
                    "static_mesh": "/Engine/BasicShapes/Cone.Cone"
                })
                if tower_top_result and tower_top_result.get("status") == "success":
                    all_actors.append(tower_top_result.get("result"))
            
            # Multiple levels of tower windows (5 levels instead of 3)
            for window_level in range(5):
                window_height = location[2] + 300 + window_level * 300
                for angle in [0, 90, 180, 270]:
                    window_x = corner[0] + 350 * math.cos(angle * math.pi / 180)
                    window_y = corner[1] + 350 * math.sin(angle * math.pi / 180)
                    window_name = f"{name_prefix}_TowerWindow_{i}_{window_level}_{angle}"
                    window_result = unreal.send_command("spawn_actor", {
                        "name": window_name,
                        "type": "StaticMeshActor",
                        "location": [window_x, window_y, window_height],
                        "rotation": [0, angle, 0],
                        "scale": [0.3, 0.5, 0.8],
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if window_result and window_result.get("status") == "success":
                        all_actors.append(window_result.get("result"))
        
        # Build INNER BAILEY corner towers (even more massive)
        logger.info("Building inner bailey towers...")
        for i, corner in enumerate(inner_corners):
            # ENORMOUS Tower base 
            tower_base_name = f"{name_prefix}_InnerTowerBase_{i}"
            tower_base_result = unreal.send_command("spawn_actor", {
                "name": tower_base_name,
                "type": "StaticMeshActor",
                "location": [corner[0], corner[1], location[2] + 200],
                "scale": [8.0, 8.0, 4.0],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if tower_base_result and tower_base_result.get("status") == "success":
                all_actors.append(tower_base_result.get("result"))
            
            # GIGANTIC Main inner tower
            inner_tower_height = tower_height * 1.4
            tower_name = f"{name_prefix}_InnerTower_{i}"
            tower_result = unreal.send_command("spawn_actor", {
                "name": tower_name,
                "type": "StaticMeshActor",
                "location": [corner[0], corner[1], location[2] + inner_tower_height/2],
                "scale": [6.0, 6.0, inner_tower_height/100],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if tower_result and tower_result.get("status") == "success":
                all_actors.append(tower_result.get("result"))
            
            # MASSIVE Tower top
            tower_top_name = f"{name_prefix}_InnerTowerTop_{i}"
            tower_top_result = unreal.send_command("spawn_actor", {
                "name": tower_top_name,
                "type": "StaticMeshActor",
                "location": [corner[0], corner[1], location[2] + inner_tower_height + 200],
                "scale": [8.0, 8.0, 3.0],
                "static_mesh": "/Engine/BasicShapes/Cone.Cone"
            })
            if tower_top_result and tower_top_result.get("status") == "success":
                all_actors.append(tower_top_result.get("result"))
        
        # Add intermediate towers along walls (more complex)
        logger.info("Adding intermediate wall towers...")
        # North wall intermediate towers
        for i in range(max(3, 3 * complexity_multiplier)):
            tower_x = location[0] - outer_width/4 + i * outer_width/4
            tower_name = f"{name_prefix}_NorthWallTower_{i}"
            tower_result = unreal.send_command("spawn_actor", {
                "name": tower_name,
                "type": "StaticMeshActor",
                "location": [tower_x, location[1] - outer_depth/2, location[2] + tower_height * 0.8/2],
                "scale": [3.0, 3.0, tower_height * 0.8/100],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if tower_result and tower_result.get("status") == "success":
                all_actors.append(tower_result.get("result"))
        
        # South wall intermediate towers
        for i in range(max(3, 3 * complexity_multiplier)):
            tower_x = location[0] - outer_width/4 + i * outer_width/4
            tower_name = f"{name_prefix}_SouthWallTower_{i}"
            tower_result = unreal.send_command("spawn_actor", {
                "name": tower_name,
                "type": "StaticMeshActor",
                "location": [tower_x, location[1] + outer_depth/2, location[2] + tower_height * 0.8/2],
                "scale": [3.0, 3.0, tower_height * 0.8/100],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if tower_result and tower_result.get("status") == "success":
                all_actors.append(tower_result.get("result"))
        
        # Build MASSIVE central keep complex 
        logger.info("Building enormous central keep complex...")
        keep_width = inner_width * 0.6
        keep_depth = inner_depth * 0.6
        keep_height = tower_height * 2.0  # Much taller (already scaled)
        
        # MASSIVE Keep base
        keep_base_name = f"{name_prefix}_KeepBase"
        keep_base_result = unreal.send_command("spawn_actor", {
            "name": keep_base_name,
            "type": "StaticMeshActor",
            "location": [location[0], location[1], location[2] + keep_height/2],
            "scale": [keep_width/100, keep_depth/100, keep_height/100],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if keep_base_result and keep_base_result.get("status") == "success":
            all_actors.append(keep_base_result.get("result"))
        
        # GIGANTIC central Keep spire/tower
        # Ensure this sits ON TOP of the keep base instead of floating.
        # Compute the spire height explicitly and place its center at (keep_top + spire_height/2).
        keep_spire_height = max(1200.0, tower_height * 1.0)
        keep_top_z = location[2] + keep_height  # top of the keep base cube
        keep_tower_name = f"{name_prefix}_KeepTower"
        keep_tower_result = unreal.send_command("spawn_actor", {
            "name": keep_tower_name,
            "type": "StaticMeshActor",
            "location": [location[0], location[1], keep_top_z + keep_spire_height / 2.0],
            "scale": [4.0, 4.0, keep_spire_height / 100.0],
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if keep_tower_result and keep_tower_result.get("status") == "success":
            all_actors.append(keep_tower_result.get("result"))
        
        # ENORMOUS Great Hall (throne room)
        great_hall_name = f"{name_prefix}_GreatHall"
        great_hall_result = unreal.send_command("spawn_actor", {
            "name": great_hall_name,
            "type": "StaticMeshActor",
            "location": [location[0], location[1] + keep_depth/3, location[2] + 200],
            "scale": [keep_width/100 * 0.8, keep_depth/100 * 0.5, 6.0],  # Much taller
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if great_hall_result and great_hall_result.get("status") == "success":
            all_actors.append(great_hall_result.get("result"))
        
        # Additional keep towers (4 corner towers of the keep)
        logger.info("Adding keep corner towers...")
        keep_corners = [
            [location[0] - keep_width/3, location[1] - keep_depth/3],
            [location[0] + keep_width/3, location[1] - keep_depth/3],
            [location[0] + keep_width/3, location[1] + keep_depth/3],
            [location[0] - keep_width/3, location[1] + keep_depth/3],
        ]
        
        for i, corner in enumerate(keep_corners):
            keep_corner_tower_name = f"{name_prefix}_KeepCornerTower_{i}"
            keep_corner_tower_result = unreal.send_command("spawn_actor", {
                "name": keep_corner_tower_name,
                "type": "StaticMeshActor",
                "location": [corner[0], corner[1], location[2] + keep_height * 0.8],
                "scale": [3.0, 3.0, keep_height/100 * 0.8],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if keep_corner_tower_result and keep_corner_tower_result.get("status") == "success":
                all_actors.append(keep_corner_tower_result.get("result"))
        
        # Build MASSIVE inner courtyard complex
        logger.info("Adding massive courtyard complex...")
        
        # HUGE Stables complex
        stable_name = f"{name_prefix}_Stables"
        stable_result = unreal.send_command("spawn_actor", {
            "name": stable_name,
            "type": "StaticMeshActor",
            "location": [location[0] - inner_width/3, location[1] + inner_depth/3, location[2] + 150],
            "scale": [8.0, 4.0, 3.0],  # Much larger
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if stable_result and stable_result.get("status") == "success":
            all_actors.append(stable_result.get("result"))
        
        # MASSIVE Barracks
        barracks_name = f"{name_prefix}_Barracks"
        barracks_result = unreal.send_command("spawn_actor", {
            "name": barracks_name,
            "type": "StaticMeshActor",
            "location": [location[0] + inner_width/3, location[1] + inner_depth/3, location[2] + 150],
            "scale": [10.0, 6.0, 3.0],  # Much larger
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if barracks_result and barracks_result.get("status") == "success":
            all_actors.append(barracks_result.get("result"))
        
        # Large Blacksmith complex
        blacksmith_name = f"{name_prefix}_Blacksmith"
        blacksmith_result = unreal.send_command("spawn_actor", {
            "name": blacksmith_name,
            "type": "StaticMeshActor",
            "location": [location[0] + inner_width/3, location[1] - inner_depth/3, location[2] + 100],
            "scale": [6.0, 6.0, 2.0],  # Much larger
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if blacksmith_result and blacksmith_result.get("status") == "success":
            all_actors.append(blacksmith_result.get("result"))
        
        # MASSIVE Well
        well_name = f"{name_prefix}_Well"
        well_result = unreal.send_command("spawn_actor", {
            "name": well_name,
            "type": "StaticMeshActor",
            "location": [location[0] - inner_width/4, location[1], location[2] + 50],
            "scale": [3.0, 3.0, 2.0],  # Much larger
            "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
        })
        if well_result and well_result.get("status") == "success":
            all_actors.append(well_result.get("result"))
        
        # ADD MANY MORE BUILDINGS FOR COMPLEXITY
        
        # Armory
        armory_name = f"{name_prefix}_Armory"
        armory_result = unreal.send_command("spawn_actor", {
            "name": armory_name,
            "type": "StaticMeshActor",
            "location": [location[0] - inner_width/3, location[1] - inner_depth/3, location[2] + 150],
            "scale": [6.0, 4.0, 3.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if armory_result and armory_result.get("status") == "success":
            all_actors.append(armory_result.get("result"))
        
        # Chapel
        chapel_name = f"{name_prefix}_Chapel"
        chapel_result = unreal.send_command("spawn_actor", {
            "name": chapel_name,
            "type": "StaticMeshActor",
            "location": [location[0], location[1] - inner_depth/3, location[2] + 200],
            "scale": [8.0, 5.0, 4.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if chapel_result and chapel_result.get("status") == "success":
            all_actors.append(chapel_result.get("result"))
        
        # Kitchen complex
        kitchen_name = f"{name_prefix}_Kitchen"
        kitchen_result = unreal.send_command("spawn_actor", {
            "name": kitchen_name,
            "type": "StaticMeshActor",
            "location": [location[0] - inner_width/4, location[1] + inner_depth/4, location[2] + 120],
            "scale": [5.0, 4.0, 2.5],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if kitchen_result and kitchen_result.get("status") == "success":
            all_actors.append(kitchen_result.get("result"))
        
        # Treasury
        treasury_name = f"{name_prefix}_Treasury"
        treasury_result = unreal.send_command("spawn_actor", {
            "name": treasury_name,
            "type": "StaticMeshActor",
            "location": [location[0] + inner_width/4, location[1] + inner_depth/4, location[2] + 100],
            "scale": [3.0, 3.0, 2.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if treasury_result and treasury_result.get("status") == "success":
            all_actors.append(treasury_result.get("result"))
        
        # Granary
        granary_name = f"{name_prefix}_Granary"
        granary_result = unreal.send_command("spawn_actor", {
            "name": granary_name,
            "type": "StaticMeshActor",
            "location": [location[0] + inner_width/4, location[1] - inner_depth/4, location[2] + 180],
            "scale": [4.0, 6.0, 3.5],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if granary_result and granary_result.get("status") == "success":
            all_actors.append(granary_result.get("result"))
        
        # Guard House
        guardhouse_name = f"{name_prefix}_GuardHouse"
        guardhouse_result = unreal.send_command("spawn_actor", {
            "name": guardhouse_name,
            "type": "StaticMeshActor",
            "location": [location[0] - inner_width/4, location[1] - inner_depth/4, location[2] + 150],
            "scale": [4.0, 4.0, 3.0],
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if guardhouse_result and guardhouse_result.get("status") == "success":
            all_actors.append(guardhouse_result.get("result"))

        # NEW: Fill outer bailey with smaller annex structures attached to the inner face of the first wall
        logger.info("Populating bailey with annex rooms and walkways...")
        annex_depth = int(500 * max(1.0, scale_factor))
        annex_width = int(700 * max(1.0, scale_factor))
        annex_height = int(300 * max(1.0, scale_factor))
        walkway_height = 160
        walkway_width = int(300 * max(1.0, scale_factor))
        spacing = int(1200 * max(1.0, scale_factor))

        def _spawn_annex_row(start_x: float, end_x: float, fixed_y: float, align: str, base_name: str):
            nonlocal all_actors
            count = 0
            x = start_x
            while (x <= end_x and start_x <= end_x) or (x >= end_x and start_x > end_x):
                annex_name = f"{name_prefix}_{base_name}_{count}"
                annex_x = x
                annex_y = fixed_y
                # Offset annex inward from the wall along its normal so it sits inside the bailey
                if align == "north":
                    annex_y += walkway_width
                elif align == "south":
                    annex_y -= walkway_width
                elif align == "east":
                    annex_x -= walkway_width
                elif align == "west":
                    annex_x += walkway_width

                result = unreal.send_command("spawn_actor", {
                    "name": annex_name,
                    "type": "StaticMeshActor",
                    "location": [annex_x, annex_y, location[2] + annex_height/2],
                    "scale": [annex_width/100, annex_depth/100, annex_height/100],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if result and result.get("status") == "success":
                    all_actors.append(result.get("result"))

                # Add a doorway arch on each annex
                arch_offset = 0 if align in ["north", "south"] else (annex_width * 0.25)
                door_x = annex_x + (50 if align == "east" else (-50 if align == "west" else arch_offset))
                door_y = annex_y + (50 if align == "south" else (-50 if align == "north" else 0))
                arch_name = f"{annex_name}_Door"
                arch = unreal.send_command("spawn_actor", {
                    "name": arch_name,
                    "type": "StaticMeshActor",
                    "location": [door_x, door_y, location[2] + 120],
                    "scale": [1.0, 0.6, 2.4],
                    "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
                })
                if arch and arch.get("status") == "success":
                    all_actors.append(arch.get("result"))

                # Next annex position
                x += spacing if start_x <= end_x else -spacing
                count += 1

        # Perimeter walkways just inside the first wall (four sides)
        # North and South
        walkway_z = location[2] + 100
        for side, fixed_y in [("north", location[1] - outer_depth/2 + walkway_width/2),
                              ("south", location[1] + outer_depth/2 - walkway_width/2)]:
            segments = int(outer_width / 400)
            for i in range(segments):
                seg_x = location[0] - outer_width/2 + (i * 400) + 200
                seg_name = f"{name_prefix}_Walkway_{side}_{i}"
                res = unreal.send_command("spawn_actor", {
                    "name": seg_name,
                    "type": "StaticMeshActor",
                    "location": [seg_x, fixed_y, walkway_z],
                    "scale": [4.0, walkway_width/100, walkway_height/100],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if res and res.get("status") == "success":
                    all_actors.append(res.get("result"))

        # East and West
        for side, fixed_x in [("east", location[0] + outer_width/2 - walkway_width/2),
                              ("west", location[0] - outer_width/2 + walkway_width/2)]:
            segments = int(outer_depth / 400)
            for i in range(segments):
                seg_y = location[1] - outer_depth/2 + (i * 400) + 200
                seg_name = f"{name_prefix}_Walkway_{side}_{i}"
                res = unreal.send_command("spawn_actor", {
                    "name": seg_name,
                    "type": "StaticMeshActor",
                    "location": [fixed_x, seg_y, walkway_z],
                    "scale": [walkway_width/100, 4.0, walkway_height/100],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if res and res.get("status") == "success":
                    all_actors.append(res.get("result"))

        # Annex rows along each inner face of the first wall
        # North wall inner face
        _spawn_annex_row(
            start_x=location[0] - outer_width/2 + spacing,
            end_x=location[0] + outer_width/2 - spacing,
            fixed_y=location[1] - outer_depth/2 + walkway_width + annex_depth/2,
            align="north",
            base_name="NorthAnnex"
        )

        # South wall inner face
        _spawn_annex_row(
            start_x=location[0] - outer_width/2 + spacing,
            end_x=location[0] + outer_width/2 - spacing,
            fixed_y=location[1] + outer_depth/2 - walkway_width - annex_depth/2,
            align="south",
            base_name="SouthAnnex"
        )

        # West wall inner face
        _spawn_annex_row(
            start_x=location[0] - outer_width/2 + walkway_width + annex_depth/2,
            end_x=location[0] - outer_width/2 + walkway_width + annex_depth/2,
            fixed_y=location[1] - outer_depth/2 + spacing,
            align="west",
            base_name="WestAnnex"
        )
        # vertical run along west: iterate y inside helper by calling multiple times
        for y in range(int(location[1] - outer_depth/2 + spacing), int(location[1] + outer_depth/2 - spacing) + 1, spacing):
            res = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_WestAnnex_{y}",
                "type": "StaticMeshActor",
                "location": [location[0] - outer_width/2 + walkway_width + annex_depth/2, y, location[2] + annex_height/2],
                "scale": [annex_depth/100, annex_width/100, annex_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if res and res.get("status") == "success":
                all_actors.append(res.get("result"))

        # East wall inner face
        for y in range(int(location[1] - outer_depth/2 + spacing), int(location[1] + outer_depth/2 - spacing) + 1, spacing):
            res = unreal.send_command("spawn_actor", {
                "name": f"{name_prefix}_EastAnnex_{y}",
                "type": "StaticMeshActor",
                "location": [location[0] + outer_width/2 - walkway_width - annex_depth/2, y, location[2] + annex_height/2],
                "scale": [annex_depth/100, annex_width/100, annex_height/100],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if res and res.get("status") == "success":
                all_actors.append(res.get("result"))
        
        # Add siege weapons if requested
        if include_siege_weapons:
            logger.info("Deploying siege weapons...")
            
            # MASSIVE Catapults on walls
            catapult_positions = [
                [location[0], location[1] - outer_depth/2 + 200, location[2] + wall_height],
                [location[0], location[1] + outer_depth/2 - 200, location[2] + wall_height],
                [location[0] - outer_width/3, location[1] - outer_depth/2 + 200, location[2] + wall_height],
                [location[0] + outer_width/3, location[1] + outer_depth/2 - 200, location[2] + wall_height],
            ]
            
            for i, pos in enumerate(catapult_positions):
                # MASSIVE Catapult base
                catapult_base_name = f"{name_prefix}_CatapultBase_{i}"
                catapult_base_result = unreal.send_command("spawn_actor", {
                    "name": catapult_base_name,
                    "type": "StaticMeshActor",
                    "location": pos,
                    "scale": [4.0, 3.0, 1.0],  # Much bigger
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if catapult_base_result and catapult_base_result.get("status") == "success":
                    all_actors.append(catapult_base_result.get("result"))
                
                # MASSIVE Catapult arm
                catapult_arm_name = f"{name_prefix}_CatapultArm_{i}"
                catapult_arm_result = unreal.send_command("spawn_actor", {
                    "name": catapult_arm_name,
                    "type": "StaticMeshActor",
                    "location": [pos[0], pos[1], pos[2] + 100],
                    "rotation": [45, 0, 0],
                    "scale": [0.4, 0.4, 6.0],  # Much bigger
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if catapult_arm_result and catapult_arm_result.get("status") == "success":
                    all_actors.append(catapult_arm_result.get("result"))
                
                # MASSIVE Ammunition pile
                for j in range(5):  # More ammo
                    ammo_name = f"{name_prefix}_CatapultAmmo_{i}_{j}"
                    ammo_result = unreal.send_command("spawn_actor", {
                        "name": ammo_name,
                        "type": "StaticMeshActor",
                        "location": [pos[0] + j * 80 - 160, pos[1] + 250, pos[2] + 40],
                        "scale": [0.6, 0.6, 0.6],  # Bigger ammo
                        "static_mesh": "/Engine/BasicShapes/Sphere.Sphere"
                    })
                    if ammo_result and ammo_result.get("status") == "success":
                        all_actors.append(ammo_result.get("result"))
            
            # MASSIVE Ballista on towers
            for i in range(4):
                corner = outer_corners[i]
                ballista_name = f"{name_prefix}_Ballista_{i}"
                ballista_result = unreal.send_command("spawn_actor", {
                    "name": ballista_name,
                    "type": "StaticMeshActor",
                    "location": [corner[0], corner[1], location[2] + tower_height],
                    "scale": [0.5, 3.0, 0.5],  # Bigger ballistae
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if ballista_result and ballista_result.get("status") == "success":
                    all_actors.append(ballista_result.get("result"))
        
        # Build MASSIVE DENSE surrounding settlement if requested
        if include_village:
            logger.info("Building massive dense outer settlement...")
            
            # DENSE Village houses (much closer and more numerous)
            village_radius = outer_width * 0.3  # Much closer!
            num_houses = (24 if castle_size == "epic" else 16) * complexity_multiplier  # MANY more houses
            
            # Inner ring of houses (very close)
            for i in range(num_houses):
                angle = (2 * math.pi * i) / num_houses
                house_x = location[0] + (outer_width/2 + village_radius) * math.cos(angle)
                house_y = location[1] + (outer_depth/2 + village_radius) * math.sin(angle)
                
                # Skip houses that would be in front of main gate
                if not (house_x < location[0] - outer_width * 0.4 and abs(house_y - location[1]) < 1000):
                    # BIGGER House base
                    house_name = f"{name_prefix}_VillageHouse_{i}"
                    house_result = unreal.send_command("spawn_actor", {
                        "name": house_name,
                        "type": "StaticMeshActor",
                        "location": [house_x, house_y, location[2] + 100],
                        "rotation": [0, angle * 180/math.pi, 0],
                        "scale": [3.0, 2.5, 2.0],  # Bigger
                        "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                    })
                    if house_result and house_result.get("status") == "success":
                        all_actors.append(house_result.get("result"))
                    
                    # House roof
                    roof_name = f"{name_prefix}_VillageRoof_{i}"
                    roof_result = unreal.send_command("spawn_actor", {
                        "name": roof_name,
                        "type": "StaticMeshActor",
                        "location": [house_x, house_y, location[2] + 250],
                        "rotation": [0, angle * 180/math.pi, 0],
                        "scale": [3.5, 3.0, 0.8],  # Bigger roof
                        "static_mesh": "/Engine/BasicShapes/Cone.Cone"
                    })
                    if roof_result and roof_result.get("status") == "success":
                        all_actors.append(roof_result.get("result"))
            
            # OUTER ring of houses (further out but still close)
            outer_village_radius = outer_width * 0.5
            for i in range(max(1, num_houses // 2)):
                angle = (2 * math.pi * i) / (num_houses // 2)
                house_x = location[0] + (outer_width/2 + outer_village_radius) * math.cos(angle)
                house_y = location[1] + (outer_depth/2 + outer_village_radius) * math.sin(angle)
                
                # BIGGER outer houses
                house_name = f"{name_prefix}_OuterVillageHouse_{i}"
                house_result = unreal.send_command("spawn_actor", {
                    "name": house_name,
                    "type": "StaticMeshActor",
                    "location": [house_x, house_y, location[2] + 100],
                    "rotation": [0, angle * 180/math.pi, 0],
                    "scale": [2.5, 2.0, 2.0],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if house_result and house_result.get("status") == "success":
                    all_actors.append(house_result.get("result"))
                
                roof_name = f"{name_prefix}_OuterVillageRoof_{i}"
                roof_result = unreal.send_command("spawn_actor", {
                    "name": roof_name,
                    "type": "StaticMeshActor",
                    "location": [house_x, house_y, location[2] + 250],
                    "rotation": [0, angle * 180/math.pi, 0],
                    "scale": [3.0, 2.5, 0.6],
                    "static_mesh": "/Engine/BasicShapes/Cone.Cone"
                })
                if roof_result and roof_result.get("status") == "success":
                    all_actors.append(roof_result.get("result"))
            
            # DENSE Market area (much closer to castle)
            market_x_start = location[0] - outer_width/2 - int(800 * scale_factor)  # Much closer!
            for i in range(8 * complexity_multiplier):  # More stalls
                stall_x = market_x_start + i * 150
                stall_y = location[1] + (200 if i % 2 == 0 else -200)  # Staggered
                
                stall_name = f"{name_prefix}_MarketStall_{i}"
                stall_result = unreal.send_command("spawn_actor", {
                    "name": stall_name,
                    "type": "StaticMeshActor",
                    "location": [stall_x, stall_y, location[2] + 80],
                    "scale": [2.0, 1.5, 1.5],  # Bigger stalls
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if stall_result and stall_result.get("status") == "success":
                    all_actors.append(stall_result.get("result"))
                
                # Stall canopy
                canopy_name = f"{name_prefix}_StallCanopy_{i}"
                canopy_result = unreal.send_command("spawn_actor", {
                    "name": canopy_name,
                    "type": "StaticMeshActor",
                    "location": [stall_x, stall_y, location[2] + 180],
                    "scale": [2.5, 2.0, 0.1],  # Bigger canopy
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if canopy_result and canopy_result.get("status") == "success":
                    all_actors.append(canopy_result.get("result"))
                    
            # ADD SMALL OUTBUILDINGS AND EXTENSIONS 
            logger.info("Adding small outbuildings and extensions...")
            
            # Small workshops around the castle
            workshop_positions = []
            ring_offsets = [int(400 * scale_factor), int(600 * scale_factor), int(800 * scale_factor)]
            for offset in ring_offsets:
                workshop_positions.extend([
                    [location[0] - outer_width/2 - offset, location[1] + offset],
                    [location[0] - outer_width/2 - offset, location[1] - offset],
                    [location[0] + outer_width/2 + offset, location[1] + offset],
                    [location[0] + outer_width/2 + offset, location[1] - offset],
                ])
            
            for i, pos in enumerate(workshop_positions):
                workshop_name = f"{name_prefix}_Workshop_{i}"
                workshop_result = unreal.send_command("spawn_actor", {
                    "name": workshop_name,
                    "type": "StaticMeshActor",
                    "location": [pos[0], pos[1], location[2] + 80],
                    "scale": [2.0, 1.8, 1.6],
                    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
                })
                if workshop_result and workshop_result.get("status") == "success":
                    all_actors.append(workshop_result.get("result"))
        
        # Add MASSIVE drawbridge
        logger.info("Adding massive drawbridge...")
        drawbridge_name = f"{name_prefix}_Drawbridge"
        drawbridge_result = unreal.send_command("spawn_actor", {
            "name": drawbridge_name,
            "type": "StaticMeshActor",
            "location": [location[0] - outer_width/2 - drawbridge_offset, location[1], location[2] + 20],
            "rotation": [0, 0, 0],
            "scale": [12.0 * scale_factor, 10.0 * scale_factor, 0.3],  # Much bigger
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        if drawbridge_result and drawbridge_result.get("status") == "success":
            all_actors.append(drawbridge_result.get("result"))
        
        # Add MASSIVE moat around castle
        logger.info("Creating massive moat...")
        moat_width = int(1200 * scale_factor)  # Much wider
        moat_sections = int(30 * complexity_multiplier)  # More sections
        
        for i in range(moat_sections):
            angle = (2 * math.pi * i) / moat_sections
            moat_x = location[0] + (outer_width/2 + moat_width/2) * math.cos(angle)
            moat_y = location[1] + (outer_depth/2 + moat_width/2) * math.sin(angle)
            
            moat_name = f"{name_prefix}_Moat_{i}"
            moat_result = unreal.send_command("spawn_actor", {
                "name": moat_name,
                "type": "StaticMeshActor",
                "location": [moat_x, moat_y, location[2] - 50],
                "scale": [moat_width/100, moat_width/100, 0.1],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if moat_result and moat_result.get("status") == "success":
                all_actors.append(moat_result.get("result"))
        
        # Add flags on towers
        logger.info("Adding decorative flags...")
        flag_colors = []
        for i in range(len(outer_corners) + 2):  # Corner towers + gate towers
            flag_pole_name = f"{name_prefix}_FlagPole_{i}"
            if i < len(outer_corners):
                flag_x = outer_corners[i][0]
                flag_y = outer_corners[i][1]
                flag_z = location[2] + tower_height + 300
            else:
                # Gate tower flags
                side = 1 if i == len(outer_corners) else -1
                flag_x = location[0] - outer_width/2
                flag_y = location[1] + side * gate_tower_offset  # Updated for new gate tower spacing
                flag_z = location[2] + tower_height + 200
            
            # Flag pole
            pole_result = unreal.send_command("spawn_actor", {
                "name": flag_pole_name,
                "type": "StaticMeshActor",
                "location": [flag_x, flag_y, flag_z],
                "scale": [0.05, 0.05, 3.0],
                "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
            })
            if pole_result and pole_result.get("status") == "success":
                all_actors.append(pole_result.get("result"))
            
            # Flag
            flag_name = f"{name_prefix}_Flag_{i}"
            flag_result = unreal.send_command("spawn_actor", {
                "name": flag_name,
                "type": "StaticMeshActor",
                "location": [flag_x + 100, flag_y, flag_z + 100],
                "scale": [0.05, 2.0, 1.5],
                "static_mesh": "/Engine/BasicShapes/Cube.Cube"
            })
            if flag_result and flag_result.get("status") == "success":
                all_actors.append(flag_result.get("result"))
        
        logger.info(f"Castle fortress creation complete! Created {len(all_actors)} actors")
        
        return {
            "success": True,
            "message": f"Epic {castle_size} {architectural_style} castle fortress created with {len(all_actors)} elements!",
            "actors": all_actors,
            "stats": {
                "size": castle_size,
                "style": architectural_style,
                "wall_sections": int(outer_width/200) * 2 + int(outer_depth/200) * 2,
                "towers": tower_count,
                "has_village": include_village,
                "has_siege_weapons": include_siege_weapons,
                "total_actors": len(all_actors)
            }
        }
        
    except Exception as e:
        logger.error(f"create_castle_fortress error: {e}")
        return {"success": False, "message": str(e)}

# Run the server
if __name__ == "__main__":
    logger.info("Starting Advanced MCP server with stdio transport")
    mcp.run(transport='stdio') 