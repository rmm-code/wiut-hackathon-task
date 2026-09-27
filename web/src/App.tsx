import { useState } from "react";
import { Sidebar, nav } from "./components/Sidebar";
import { Icon } from "./components/Icon";
import { Dashboard } from "./pages/Dashboard";
import { LiveDemo } from "./pages/LiveDemo";
import { Samples } from "./pages/Samples";
import { Report } from "./pages/Report";
import { Team } from "./pages/Team";
import { useWorkspace } from "./hooks/useWorkspace";

export function App() {
  const w = useWorkspace();
  const [menu, setMenu] = useState(false);
  const [hidden, setHidden] = useState(() => {
    try {
      return localStorage.getItem("pitstop.menu") === "hidden";
    } catch {
      return false;
    }
  });
  function hideMenu(value: boolean) {
    setHidden(value);
    try {
      localStorage.setItem("pitstop.menu", value ? "hidden" : "shown");
    } catch {
      /* Remembering the choice is optional. */
    }
  }
  return (
    <div className={`app-shell ${hidden ? "menu-hidden" : ""}`}>
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
        onHide={() => hideMenu(true)}
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
            {hidden && (
              <button
                className="icon-button show-menu"
                onClick={() => hideMenu(false)}
                aria-label="Show the menu"
                title="Show the menu"
              >
                <Icon name="menu" />
              </button>
            )}
            <h1>{nav.find((item) => item.id === w.page)?.label}</h1>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          {w.page === "dashboard" && <Dashboard workspace={w} />}
          {w.page === "demo" && <LiveDemo workspace={w} />}
          {w.page === "samples" && (
            <Samples
              onSample={w.choose}
              report={w.analysis.report}
              filename={w.video.name}
            />
          )}
          {w.page === "report" && <Report />}
          {w.page === "team" && <Team />}
        </main>
      </div>
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
