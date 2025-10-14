import { NavLink } from "react-router-dom";

// active link highlighting logic
const linkClasses = ({ isActive }) =>
  "px-3 py-2 rounded-xl font-semibold transition-colors " +
  (isActive ? "bg-white/15 text-white" : "text-white/90 hover:bg-white/10");

// top navigation bar
export default function Navbar() {
  return (
    <div className="sticky top-0 z-40 bg-gradient-to-b from-bronze-600 to-bronze-700 text-white shadow-md backdrop-blur border-b border-bronze-800/40">
      <div className="px-12 h-14 flex items-center justify-between">
        {/* brand */}
        <NavLink to="/upload" className="font-black tracking-wide text-lg select-none">
          SmartResearch
        </NavLink>

        {/* nav links */}
        <nav className="flex items-center gap-2 text-sm font-medium">
          <NavLink to="/upload" className={linkClasses}>Upload</NavLink>
          <NavLink to="/papers" className={linkClasses}>All Papers</NavLink>
          <NavLink to="/cluster" className={linkClasses}>Cluster</NavLink>
          <NavLink to="/export" className={linkClasses}>Export</NavLink>
        </nav>
      </div>
    </div>
  );
}
