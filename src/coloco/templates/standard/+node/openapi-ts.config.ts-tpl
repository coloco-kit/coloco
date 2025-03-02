import { defaultPlugins } from '@hey-api/openapi-ts';
import { codegenConfig } from '@coloco/api-client-svelte';

export default {
  plugins: [
    ...defaultPlugins,
    '@hey-api/client-fetch',
    codegenConfig({ name: 'coloco-codegen', outputPath: './api' }),
  ],
};