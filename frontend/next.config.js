/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use standalone mode for Electron (includes Node.js server)
  output: 'standalone',
  // Optimize for production
  compress: true,
  // Disable image optimization for smaller build
  images: {
    unoptimized: true,
  },
  // Generate manifests for better caching
  generateBuildId: async () => {
    return 'build-' + Date.now()
  },
}

module.exports = nextConfig

