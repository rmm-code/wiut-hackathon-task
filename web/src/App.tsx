import { useState } from "react";
import { Sidebar, nav } from "./components/Sidebar";
import { Icon } from "./components/Icon";
import { Upload } from "./components/Upload";
import { Dashboard } from "./pages/Dashboard";
import { Samples } from "./pages/Samples";
import { Report } from "./pages/Report";
import { Team } from "./pages/Team";
import { useWorkspace } from "./hooks/useWorkspace";

export function App() {
  const w = useWorkspace();
  const [menu, setMenu] = useState(false);
  const [dialog, setDialog] = useState<"video" | "results" | null>(null);
  return (
    <div className="app-shell">
      <a
        href="#main"
        className="skip-link"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      <Sidebar
        page={w.page}
        navigate={w.navigate}
        videoId={w.video.id}
        onSample={w.choose}
        open={menu}
        onClose={() => setMenu(false)}
      />
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button mobile-menu"
              onClick={() => setMenu(!menu)}
              aria-label="Open navigation"
              aria-expanded={menu}
            >
              <Icon name="menu" />
            </button>
            <button
              className="icon-button back-button"
              onClick={() => w.navigate("dashboard")}
              disabled={w.page === "dashboard"}
              aria-label="Back to dashboard"
            >
              <Icon name="left" size={15} />
            </button>
            <span className="bar-divider" />
            <h1>{nav.find((item) => item.id === w.page)?.label}</h1>
          </div>
          <div className="topbar-actions">
            <span
              className="data-status"
              title="Illustrative preview and actual model results are labeled separately."
            >
              {w.analysis.origin === "preview"
                ? "Illustrative preview"
                : w.analysis.origin === "model"
                  ? "Model results · baseline"
                  : w.analysis.origin === "imported"
                    ? "Imported results"
                    : "Ready to analyze"}
            </span>
            {w.page === "dashboard" && (
              <button
                className="button small import-button"
                onClick={() => setDialog("results")}
              >
                <Icon name="json" size={15} />
                <span>Import results</span>
              </button>
            )}
            <button
              className="button small primary"
              onClick={() => setDialog("video")}
            >
              <Icon name="upload" size={15} />
              Upload video
            </button>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          {w.page === "dashboard" && <Dashboard workspace={w} />}
          {w.page === "samples" && (
            <Samples
              onSample={w.choose}
              report={w.analysis.report}
              filename={w.video.name}
            />
          )}
          {w.page === "report" && <Report />}
          {w.page === "team" && <Team />}
          <footer className="page-footer">
            <span>Team Pitstop © 2026</span>
            <span>WIUT Hackathon · CV Track</span>
          </footer>
        </main>
      </div>
      {dialog && (
        <Upload
          key={dialog}
          kind={dialog}
          filename={w.video.name}
          onClose={() => setDialog(null)}
          onFile={dialog === "video" ? w.upload : w.importResults}
        />
      )}
      {w.toast && (
        <div className="toast" role="status">
          <Icon name="info" size={18} />
          <span>{w.toast}</span>
          <button
            className="icon-button"
            onClick={() => w.setToast("")}
            aria-label="Dismiss notification"
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
