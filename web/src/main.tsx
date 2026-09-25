import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "@fontsource/inter/latin-700.css";
import "./styles/base.css";
import "./styles/layout.css";
import "./styles/dashboard.css";
import "./styles/events.css";
import "./styles/pages.css";
import "./styles/jobs.css";
import "./styles/review.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
