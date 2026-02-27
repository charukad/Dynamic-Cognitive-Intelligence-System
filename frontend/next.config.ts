import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,

  // Skip type checking during build (run separately via tsc)
  typescript: { ignoreBuildErrors: true },

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
    // Server-side: use internal Docker network URL (not NEXT_PUBLIC_* which is for browser)
    const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
