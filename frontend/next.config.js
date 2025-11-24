/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  compress: true,
  images: {
    unoptimized: true,
  },
  trailingSlash: false,
  generateBuildId: async () => {
    return 'build-' + Date.now()
  },
}

module.exports = nextConfig

