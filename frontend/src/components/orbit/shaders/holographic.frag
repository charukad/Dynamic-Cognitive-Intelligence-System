varying vec2 vUv;
varying vec3 vColor;
varying float vAlpha;

void main() {
  // Circular particle shape with soft edge
  vec2 center = gl_PointCoord - 0.5;
  float dist = length(center);
  
  // Discard corners to make a circle
  if (dist > 0.5) discard;
  
  // Soft glow gradient (1.0 at center, 0.0 at edge)
  float glow = 1.0 - (dist * 2.0);
  glow = pow(glow, 1.5); // Sharpen the core
  
  // Additive blending effect
  gl_FragColor = vec4(vColor, vAlpha * glow);
  
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
