// jest.polyfills.js
/**
 * to integrate msw 2.x
 * ref. https://mswjs.io/docs/faq#requestresponsetextencoder-is-not-defined-jest
 */

const { TextDecoder, TextEncoder } = require('node:util');
const { clearImmediate } = require("node:timers");

Object.defineProperties(globalThis, {
    TextDecoder: { value: TextDecoder },
    TextEncoder: { value: TextEncoder },
    clearImmediate: { value: clearImmediate },
});

const { ReadableStream } = require('node:stream/web');
if (globalThis.ReadableStream === undefined) {
    globalThis.ReadableStream = ReadableStream
}

const { Blob, File } = require('node:buffer');
const { fetch, Headers, FormData, Request, Response } = require('undici');

Object.defineProperties(globalThis, {
    fetch: { value: fetch, writable: true },
    Blob: { value: Blob },
    File: { value: File },
    Headers: { value: Headers },
    FormData: { value: FormData },
    Request: { value: Request },
    Response: { value: Response },
});
