import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, PlusCircle, Search, Library, Activity, Microscope } from "lucide-react";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/new", label: "New Investigation", icon: PlusCircle },
  { to: "/evidence", label: "Evidence Explorer", icon: Search },
  { to: "/knowledge-base", label: "Knowledge Base", icon: Library },
  { to: "/agents", label: "Agent Monitor", icon: Activity },
];

export default function Layout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-base-950 text-ink-100">
      <aside className="flex w-60 shrink-0 flex-col border-r border-base-700 bg-base-900">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-500/20 text-accent-400">
            <Microscope size={18} />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight">VeriScope AI</div>
            <div className="text-[10px] text-ink-400">Agentic Research Verifier</div>
          </div>
        </div>
        <nav className="flex flex-col gap-1 px-3 py-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent-500/15 text-accent-400"
                    : "text-ink-300 hover:bg-base-800 hover:text-ink-100"
                }`
              }
            >
              <item.icon size={16} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-4 py-4 text-[11px] text-ink-500">
          Question → Plan → Research → Evidence
          <br />
          → Verification → Contract
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <Outlet />
      </main>
    </div>
  );
}
