import type { Plugin } from '@hey-api/openapi-ts';
import type { Config } from './types';
import fs from 'fs';
import path from 'path';

export const handler: Plugin.Handler<Config> = ({ context, plugin }) => {
  const operationsByPath: Record<string, string[]> = {};
  context.subscribe('operation', ({ operation }) => {
    const module = operation.summary?.match(/\((.+?)\)$/)?.[1];
    if (module) {
      const outputPath = path.join(context.config.output.path, `../api/${module.replace('.', '/')}.ts`);
      const importRelative = path.relative(path.dirname(outputPath), context.config.output.path);
      // ensure the directory exists
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });

      // write file
      if (!operationsByPath[outputPath]) {
        operationsByPath[outputPath] = [];
      }
      operationsByPath[outputPath].push(operation.id);
      const operations = operationsByPath[outputPath];
      fs.writeFileSync(
        outputPath,
        `import { ${operations.join(', ')} } from "${importRelative}/sdk.gen";\n` +
        `import { apiCall } from "@fakit/client";\n` +
        operations.map(operation => `const ${operation}Wrapped = apiCall(${operation});\n`).join('') +
        `export { ${operations.map(operation => `${operation}Wrapped as ${operation}`).join(', ')} };`
      );
      console.log("WROTE", outputPath);
    }
  });

  console.log("PLUGIN RAN!!!");
};


function test(handler: Plugin.Handler<Config>) {
  return handler;
}
const z = test(handler);

export { z as poop };