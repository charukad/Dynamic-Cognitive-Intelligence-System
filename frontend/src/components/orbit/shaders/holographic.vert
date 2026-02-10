varying vec2 vUv;
varying vec3 vColor;
varying float vAlpha;

attribute vec3 color;  // Per-vertex color from buffer geometry
attribute float size;
attribute float alpha;

void main() {
  vUv = uv;
  vColor = color;
  vAlpha = alpha;

  vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
  
  // Size attenuation based on distance
  gl_PointSize = size * (300.0 / -mvPosition.z);
  
  gl_Position = projectionMatrix * mvPosition;
}
