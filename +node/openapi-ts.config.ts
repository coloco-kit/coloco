import { defaultPlugins } from '@hey-api/openapi-ts';
import { defineConfig } from '../+app/fakit/codegen';

export default {
  //input: '/tmp/openapi.json',
  //output: '../+app/.generated/client',
  plugins: [
    ...defaultPlugins,
    '@hey-api/client-fetch',
    defineConfig({ name: 'fakit-codegen', outputPath: './api' }),
  ],
};