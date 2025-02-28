// TODO: custom adapter
import type { Options as ClientOptions, TDataShape, Client, RequestResult, Config } from '@hey-api/client-fetch';
import { type Writable, writable } from 'svelte/store';
import { createClient } from '@hey-api/client-fetch';

export type Options<TData extends TDataShape = TDataShape, ThrowOnError extends boolean = boolean> = ClientOptions<TData, ThrowOnError> & {
  /**
   * You can provide a client instance returned by `createClient()` instead of
   * individual options. This might be also useful if you want to implement a
   * custom client.
   */
  client?: Client;
  /**
   * You can pass arbitrary values through the `meta` object. This can be
   * used to access values that aren't defined as part of the SDK function.
   */
  meta?: Record<string, unknown>;
};


export function apiCall<A, R>(
  call: (data: A) => RequestResult<R>,
): (data?: A) => Writable<{ loading: boolean, data: R | undefined, error: string | undefined }> {
  return (data: A = {} as A) => {
    const store = writable({ loading: true, data: undefined, error: undefined });
    call({ client: _client, ...data }).then((result) => {
      // @ts-ignore
      store.set({ loading: false, data: result.data, error: result.error });
    });
    return store;
  }
}

let _client: Client | undefined;
export function setupClient(config: Config) {
  _client = createClient(config);
}
