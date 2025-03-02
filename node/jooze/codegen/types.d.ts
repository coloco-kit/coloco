export interface Config {
  /**
   * Plugin name. Must be unique.
   */
  name: 'jooze-codegen';
  /**
   * Name of the generated file.
   *
   * @default 'jooze-codegen'
   */
  output?: string;
  /**
   * Path to the output directory.
   *
   * @default './api'
   */
  outputPath?: string;
}