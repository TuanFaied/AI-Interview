/** @type {import('next').NextConfig} */
const nextConfig: import('next').NextConfig = {
  async rewrites() {
    return [
      {
        source: '/static/tts/:path*',
        destination: 'http://localhost:8000/static/tts/:path*',
      },
    ]
  },
}

module.exports = nextConfig