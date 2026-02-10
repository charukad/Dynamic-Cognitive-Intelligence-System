// Vertex Shader for Agent Particles
// Implements GPU-accelerated particle rendering with instancing

varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vColor;

void main() {
  // Pass instance color to fragment shader
  vColor = instanceColor;
  
  // Transform normal to world space
  vNormal = normalize(normalMatrix * normal);
  
  // Calculate world position
  vec4 worldPosition = modelMatrix * instanceMatrix * vec4(position, 1.0);
  vPosition = worldPosition.xyz;
  
  // Project to screen space
  gl_Position = projectionMatrix * viewMatrix * worldPosition;
}
