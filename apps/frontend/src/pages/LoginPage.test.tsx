import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, test } from "vitest";
import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  test("links the Strava login action to the backend OAuth endpoint", () => {
    const html = renderToStaticMarkup(<LoginPage />);

    expect(html).toContain('href="/api/auth/strava"');
    expect(html).toContain("Continue with Strava");
  });
});
