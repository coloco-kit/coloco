import path, { dirname, resolve, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '../');

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  root: resolve(root, '+app'),
  resolve: {
    // @ts-ignore
    alias: [{
      find: './api',
      customResolver: (_, filePath: string) => {
        const subFolder = path.relative(root, dirname(filePath));
        const apiFile = resolve(root, `+app/.generated/api/${subFolder}/api.ts`);
        return apiFile;
      }
    },
    // @ts-ignore
    {
      find: '@fakit',
      replacement: '/fakit'
    },
    // @ts-ignore
    {
      find: '@api',
      replacement: '/.generated/api'
    }]
  }
})
