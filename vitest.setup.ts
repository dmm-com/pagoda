/**
 * Vitest setup: MSW 2.x integration and Testing Library matchers.
 * ref. https://mswjs.io/docs/faq#requestresponsetextencoder-is-not-defined-jest
 */
import "@testing-library/jest-dom/vitest";

import { TextDecoder, TextEncoder } from "node:util";
import { clearImmediate } from "node:timers";
import { ReadableStream, TransformStream } from "node:stream/web";
import { Blob, File } from "node:buffer";
import { fetch, Headers, FormData, Request, Response } from "undici";

Object.defineProperties(globalThis, {
  TextDecoder: { value: TextDecoder },
  TextEncoder: { value: TextEncoder },
  clearImmediate: { value: clearImmediate },
});

if (globalThis.ReadableStream === undefined) {
  globalThis.ReadableStream =
    ReadableStream as unknown as typeof globalThis.ReadableStream;
}
if (globalThis.TransformStream === undefined) {
  globalThis.TransformStream =
    TransformStream as unknown as typeof globalThis.TransformStream;
}

// undici binds markResourceTiming at module-eval time; jsdom does not implement it.
// (Not part of the standard lib.dom Performance type.)
const performanceWithMarkResourceTiming = performance as Performance & {
  markResourceTiming?: () => void;
};
if (
  typeof performance !== "undefined" &&
  typeof performanceWithMarkResourceTiming.markResourceTiming !== "function"
) {
  performanceWithMarkResourceTiming.markResourceTiming = () => {};
}

globalThis.fetch = fetch as unknown as typeof globalThis.fetch;
globalThis.Blob = Blob as unknown as typeof globalThis.Blob;
globalThis.File = File as unknown as typeof globalThis.File;
globalThis.Headers = Headers as unknown as typeof globalThis.Headers;
globalThis.FormData = FormData as unknown as typeof globalThis.FormData;
globalThis.Request = Request as unknown as typeof globalThis.Request;
globalThis.Response = Response as unknown as typeof globalThis.Response;

class BroadcastChannel {
  name: string;
  listeners: Record<string, Array<(event: unknown) => void>>;

  constructor(name: string) {
    this.name = name;
    this.listeners = {};
  }

  postMessage(_message: unknown) {}

  addEventListener(type: string, listener: (event: unknown) => void) {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(listener);
  }

  removeEventListener(type: string, listener: (event: unknown) => void) {
    if (!this.listeners[type]) {
      return;
    }
    this.listeners[type] = this.listeners[type].filter((l) => l !== listener);
  }

  close() {
    this.listeners = {};
  }
}

if (!globalThis.BroadcastChannel) {
  globalThis.BroadcastChannel =
    BroadcastChannel as typeof globalThis.BroadcastChannel;
}
