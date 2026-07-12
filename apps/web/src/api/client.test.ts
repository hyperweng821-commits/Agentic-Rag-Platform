import { API_BASE_URL } from "@/api/client";

describe("API client configuration", () => {
  it("uses the versioned API path by default", () => {
    expect(API_BASE_URL).toBe("/api/v1");
  });
});
