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
}