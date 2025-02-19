import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

const __dirname = dirname(fileURLToPath(import.meta.url))

console.log(resolve(__dirname, '../+app/index.html'))

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  root: resolve(__dirname, '../+app'),
})
