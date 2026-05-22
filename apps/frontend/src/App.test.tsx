import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router-dom/server";
import { describe, expect, test } from "vitest";
import { App } from "./App";

describe("App", () => {
  test("renders the login page at /login", () => {
    const html = renderToStaticMarkup(
      <StaticRouter location="/login">
        <App />
      </StaticRouter>,
    );

    expect(html).toContain("使用 Strava 登入");
  });
});
