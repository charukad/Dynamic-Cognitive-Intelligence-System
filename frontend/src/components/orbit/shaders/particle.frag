// Fragment Shader for Agent Particles
// Advanced lighting with glow effect based on agent state

uniform vec3 lightPosition;
uniform float glowIntensity;

varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vColor;

void main() {
  // Normalize interpolated normal
  vec3 normal = normalize(vNormal);
  
  // Calculate light direction
  vec3 lightDir = normalize(lightPosition - vPosition);
  
  // Diffuse lighting (Lambertian)
  float diffuse = max(dot(normal, lightDir), 0.0);
  
  // Specular lighting (Blinn-Phong)
  vec3 viewDir = normalize(cameraPosition - vPosition);
  vec3 halfDir = normalize(lightDir + viewDir);
  float specular = pow(max(dot(normal, halfDir), 0.0), 32.0);
  
  // Fresnel glow (edge lighting)
  float fresnel = pow(1.0 - max(dot(viewDir, normal), 0.0), 3.0);
  
  // Combine lighting
  vec3 lighting = vColor * (0.3 + diffuse * 0.6); // Ambient + diffuse
  lighting += vec3(1.0) * specular * 0.5;          // Specular highlights
  lighting += vColor * fresnel * glowIntensity;    // Glow effect
  
  // Output final color with alpha
  gl_FragColor = vec4(lighting, 1.0);
}
