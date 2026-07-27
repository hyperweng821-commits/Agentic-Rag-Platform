import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("App", () => {
  it("renders the initialized project shell", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "AgentForge" }),
    ).toBeInTheDocument();
  });
});
