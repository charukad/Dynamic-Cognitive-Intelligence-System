"""Particle data streaming via WebSocket with MsgPack."""

import struct
from typing import Any, Dict, List

try:
    import msgpack
except ImportError:
    msgpack = None

from src.core import get_logger

logger = get_logger(__name__)


class ParticleStreamer:
    """
    Particle data streamer using MsgPack for efficient binary serialization.
    
    Handles streaming of particle positions, velocities, and metadata
    for real-time 3D visualization.
    """

    def __init__(self) -> None:
        """Initialize particle streamer."""
        if msgpack is None:
            logger.warning("msgpack not installed. Install with: pip install msgpack")
        
        # Particle state
        self.particles: Dict[str, Dict[str, Any]] = {}

    def serialize_particles(
        self,
        particles: List[Dict[str, Any]],
    ) -> bytes:
        """
        Serialize particle data to binary format.
        
        Args:
            particles: List of particle data
            
        Returns:
            Binary serialized data
        """
        if msgpack:
            # Use MsgPack for efficient serialization
            try:
                return msgpack.packb(particles, use_bin_type=True)
            except Exception as e:
                logger.error(f"MsgPack serialization failed: {e}")
        
        # Fallback to simple struct packing
        # Format: [count][id, x, y, z, vx, vy, vz, type, ...] per particle
        buffer = struct.pack('I', len(particles))  # Particle count
        
        for particle in particles:
            # Pack particle ID (8 bytes)
            p_id = particle.get('id', '').encode('utf-8')[:8].ljust(8, b'\x00')
            buffer += p_id
            
            # Pack position (3 floats)
            pos = particle.get('position', [0.0, 0.0, 0.0])
            buffer += struct.pack('fff', *pos[:3])
            
            # Pack velocity (3 floats)
            vel = particle.get('velocity', [0.0, 0.0, 0.0])
            buffer += struct.pack('fff', *vel[:3])
            
            # Pack type (1 int)
            p_type = particle.get('type', 0)
            buffer += struct.pack('i', p_type)
        
        return buffer

    def deserialize_particles(self, data: bytes) -> List[Dict[str, Any]]:
        """
        Deserialize particle data from binary format.
        
        Args:
            data: Binary particle data
            
        Returns:
            List of particle dictionaries
        """
        if msgpack:
            try:
                return msgpack.unpackb(data, raw=False)
            except Exception as e:
                logger.error(f"MsgPack deserialization failed: {e}")
        
        # Fallback struct unpacking
        particles = []
        
        # Read particle count
        count = struct.unpack('I', data[:4])[0]
        offset = 4
        
        # Each particle: 8 bytes ID + 24 bytes position/velocity + 4 bytes type = 36 bytes
        particle_size = 36
        
        for _ in range(count):
            if offset + particle_size > len(data):
                break
            
            # Unpack particle
            p_id = data[offset:offset+8].rstrip(b'\x00').decode('utf-8')
            offset += 8
            
            px, py, pz = struct.unpack('fff', data[offset:offset+12])
            offset += 12
            
            vx, vy, vz = struct.unpack('fff', data[offset:offset+12])
            offset += 12
            
            p_type = struct.unpack('i', data[offset:offset+4])[0]
            offset += 4
            
            particles.append({
                'id': p_id,
                'position': [px, py, pz],
                'velocity': [vx, vy, vz],
                'type': p_type,
            })
        
        return particles

    def update_particle(
        self,
        particle_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Update particle state.
        
        Args:
            particle_id: Particle identifier
            data: Particle data
        """
        self.particles[particle_id] = {
            'id': particle_id,
            **data,
        }

    def get_all_particles(self) -> List[Dict[str, Any]]:
        """
        Get all particle data.
        
        Returns:
            List of all particles
        """
        return list(self.particles.values())

    def remove_particle(self, particle_id: str) -> None:
        """
        Remove particle.
        
        Args:
            particle_id: Particle to remove
        """
        if particle_id in self.particles:
            del self.particles[particle_id]

    def create_particle_update_message(
        self,
        particle_updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create particle update message for WebSocket.
        
        Args:
            particle_updates: List of particle updates
            
        Returns:
            WebSocket message
        """
        # Serialize to binary
        binary_data = self.serialize_particles(particle_updates)
        
        return {
            'type': 'particle_update',
            'count': len(particle_updates),
            'data': binary_data,
            'encoding': 'msgpack' if msgpack else 'struct',
        }


# Global instance
particle_streamer = ParticleStreamer()
