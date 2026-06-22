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

const { ReadableStream, TransformStream } = require('node:stream/web');
if (globalThis.ReadableStream === undefined) {
    globalThis.ReadableStream = ReadableStream
}
if (globalThis.TransformStream === undefined) {
    globalThis.TransformStream = TransformStream
}

// Add polyfill for performance.markResourceTiming used by undici.
// undici binds `markResourceTiming` from `performance` once at module-eval time
// (web/fetch/index.js: `const markResourceTiming = performance.markResourceTiming`),
// and jsdom does not implement it. This MUST run before `require('undici')`,
// otherwise undici captures `undefined` and every fetch completion throws
// "markResourceTiming is not a function" from a deferred callback — which, when
// it fires after the test environment is torn down, crashes the jest worker.
if (typeof performance !== 'undefined' && typeof performance.markResourceTiming !== 'function') {
  performance.markResourceTiming = () => {};
}

// Add required web API globals for MSW
const { Blob, File } = require('node:buffer');
const { fetch, Headers, FormData, Request, Response } = require('undici');

// Define these globals for MSW
globalThis.fetch = fetch;
globalThis.Blob = Blob;
globalThis.File = File;
globalThis.Headers = Headers;
globalThis.FormData = FormData;
globalThis.Request = Request;
globalThis.Response = Response;

// MSW v2 requires BroadcastChannel
class BroadcastChannel {
  constructor(name) {
    this.name = name;
    this.listeners = {};
  }

  postMessage(message) {
    // Mock implementation
  }

  addEventListener(type, listener) {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(listener);
  }

  removeEventListener(type, listener) {
    if (!this.listeners[type]) {
      return;
    }
    this.listeners[type] = this.listeners[type].filter(l => l !== listener);
  }

  close() {
    this.listeners = {};
  }
}

// Add BroadcastChannel to global scope
if (!globalThis.BroadcastChannel) {
    globalThis.BroadcastChannel = BroadcastChannel;
}