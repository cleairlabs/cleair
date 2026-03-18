import { afterEach, describe, expect, test, vi } from "vitest";
import { loadSessionStatus } from "./useAccessGate";

describe("loadSessionStatus", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("returns true when the backend reports an authenticated session", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ authenticated: true }),
    }));

    await expect(loadSessionStatus("http://localhost:8000")).resolves.toBe(true);
  });

  test("returns false when the backend reports an unauthenticated session", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ authenticated: false }),
    }));

    await expect(loadSessionStatus("http://localhost:8000")).resolves.toBe(false);
  });
});
