import { render, screen } from "@testing-library/react";

import { AppRouter } from "@/app/router";

describe("AppRouter", () => {
  it("renders the root route", async () => {
    render(<AppRouter />);

    expect(
      await screen.findByRole("heading", { name: "AgentForge" }),
    ).toBeVisible();
  });
});
