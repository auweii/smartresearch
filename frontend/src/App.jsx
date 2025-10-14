import { Routes, Route, Navigate } from "react-router-dom"
import Navbar from "./components/Navbar"
import UploadPage from "./pages/UploadPage"
import AllPapersPage from "./pages/AllPapersPage"
import ClusterPage from "./pages/ClusterPage"
import ExportPage from "./pages/ExportPage"

// app root — handles routing between main views
export default function App() {
  return (
    <div className="min-h-full">
      <Navbar />
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/papers" element={<AllPapersPage />} />
        <Route path="/cluster" element={<ClusterPage />} />
        <Route path="/export" element={<ExportPage />} />
      </Routes>
    </div>
  )
}
