import { defineConfig } from "orval";

export default defineConfig({
  runningAnalyticsApi: {
    input: "../../api-contract/openapi.json",
    output: {
      target: "src/api/generated.ts",
      client: "react-query",
      prettier: false,
      override: {
        mutator: {
          path: "src/api/http.ts",
          name: "apiClient",
        },
      },
    },
  },
});
