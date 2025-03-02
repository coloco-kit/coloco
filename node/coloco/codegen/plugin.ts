import type { Plugin } from '@hey-api/openapi-ts';
import type { Config } from './types';
import fs from 'fs';
import path from 'path';

export const handler: Plugin.Handler<Config> = ({ context, plugin }) => {
  const operationsByPath: Record<string, string[]> = {};

  context.subscribe('operation', ({ operation }) => {
    const module = operation.summary?.match(/\((.+?)\)$/)?.[1];
    if (module) {
      const outputPath = path.join(context.config.output.path, `${plugin.outputPath}/${module.replace('.', '/')}.ts`);
      // ensure the directory exists
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });

      if (!operationsByPath[outputPath]) {
        operationsByPath[outputPath] = [];
      }
      operationsByPath[outputPath].push(operation.id);
    }
  });

  context.subscribe('after', () => {
    for (const [outputPath, operations] of Object.entries(operationsByPath)) {
      const importRelative = path.relative(path.dirname(outputPath), context.config.output.path);
      fs.writeFileSync(
        outputPath,
        `import { ${operations.join(', ')} } from "${importRelative}/sdk.gen";\n` +
        `import { apiCall } from "@coloco/client";\n` +
        operations.map(operation => `const ${operation}Wrapped = apiCall(${operation});\n`).join('') +
        `export { ${operations.map(operation => `${operation}Wrapped as ${operation}`).join(', ')} };`
      );
    }
  });
};


function test(handler: Plugin.Handler<Config>) {
  return handler;
}
const z = test(handler);

export { z as poop };