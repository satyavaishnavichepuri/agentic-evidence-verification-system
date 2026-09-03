import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import NewInvestigation from "./pages/NewInvestigation";
import Workspace from "./pages/Workspace";
import EvidenceExplorer from "./pages/EvidenceExplorer";
import KnowledgeBase from "./pages/KnowledgeBase";
import AgentMonitor from "./pages/AgentMonitor";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewInvestigation />} />
        <Route path="/investigations/:id" element={<Workspace />} />
        <Route path="/evidence" element={<EvidenceExplorer />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
        <Route path="/agents" element={<AgentMonitor />} />
      </Route>
    </Routes>
  );
}
