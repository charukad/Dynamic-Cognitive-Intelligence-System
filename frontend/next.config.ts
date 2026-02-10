import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,

  // Turbopack configuration for shader files (Next.js 16+)
  turbopack: {
    rules: {
      // Handle shader files as raw text
      '*.{glsl,vs,fs,vert,frag}': {
        loaders: ['raw-loader'],
        as: '*.txt',
      },
    },
  },

  // Webpack configuration (fallback for webpack mode)
  webpack: (config) => {
    config.module.rules.push({
      test: /\.(glsl|vs|fs|vert|frag)$/,
      use: ['raw-loader'],
    });
    return config;
  },
  // API Proxy Configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8008/api/:path*',
      },
    ];
  },
};

export default nextConfig;
