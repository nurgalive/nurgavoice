import { defineConfig } from 'vite'

export default defineConfig({
  // Ensure assets are properly handled
  assetsInclude: ['**/*.css'],
  
  // Build configuration
  build: {
    // Output directory
    outDir: 'dist',
    
    // Generate source maps for debugging
    sourcemap: true,
    
    // Rollup options
    rollupOptions: {
      input: {
        main: 'index.html'
      }
    }
  },
  
  // Development server configuration
  server: {
    port: 3000,
    open: true
  },
  
  // Base URL for assets
  base: './'
})