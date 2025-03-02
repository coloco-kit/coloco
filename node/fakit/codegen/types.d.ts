export interface Config {
  /**
   * Plugin name. Must be unique.
   */
  name: 'fakit-codegen';
  /**
   * Name of the generated file.
   *
   * @default 'fakit-codegen'
   */
  output?: string;
  /**
   * Path to the output directory.
   *
   * @default './api'
   */
  outputPath?: string;
}