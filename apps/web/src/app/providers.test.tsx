import { render, screen } from "@testing-library/react";

import { AppProviders } from "@/app/providers";

describe("AppProviders", () => {
  it("renders child content", () => {
    render(
      <AppProviders>
        <p>provider child</p>
      </AppProviders>,
    );

    expect(screen.getByText("provider child")).toBeInTheDocument();
  });
});
