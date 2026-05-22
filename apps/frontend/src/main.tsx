import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <main className="min-h-screen p-6">
        <h1 className="text-2xl font-semibold">Running Analytics AI</h1>
      </main>
    </QueryClientProvider>
  </React.StrictMode>,
);
