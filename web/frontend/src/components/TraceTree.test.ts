import { describe, expect, test } from "vitest";
import { getConnectorClasses } from "./TraceTree";

describe("getConnectorClasses", () => {
  test("uses the parent-continuation flag for the first pass-through column", () => {
    const connectorClasses = getConnectorClasses(2, true, [false, true]);
    expect(connectorClasses).toEqual(["connector-pass", "connector-last"]);
  });

  test("renders an empty pass-through when parent branch does not continue", () => {
    const connectorClasses = getConnectorClasses(2, false, [true, false]);
    expect(connectorClasses).toEqual(["connector-empty", "connector-mid"]);
  });

  test("supports deeper nesting with mixed ancestor continuation", () => {
    const connectorClasses = getConnectorClasses(4, true, [false, true, false, true]);
    expect(connectorClasses).toEqual([
      "connector-pass",
      "connector-empty",
      "connector-pass",
      "connector-last",
    ]);
  });
});
