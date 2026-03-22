import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { LLMProvider } from './lib/llmContext'
import Sidebar from './components/layout/Sidebar'
import ApiKeyBanner from './components/layout/ApiKeyBanner'

import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import GraphBuilder from './pages/GraphBuilder'
import EnvironmentSetup from './pages/EnvironmentSetup'
import SimulationRunner from './pages/SimulationRunner'
import ReportView from './pages/ReportView'
import Interaction from './pages/Interaction'
import AgentGallery from './pages/AgentGallery'
import Settings from './pages/Settings'

function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg)' }}>
      <Sidebar />
      <main className="flex-1 ml-60 min-h-screen overflow-auto">
        <ApiKeyBanner />
        <div className="p-6 max-w-screen-xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <LLMProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/dashboard" element={<AppLayout><Dashboard /></AppLayout>} />
            <Route path="/projects" element={<AppLayout><Projects /></AppLayout>} />
            <Route path="/projects/:id" element={<AppLayout><ProjectDetail /></AppLayout>} />
            <Route path="/projects/:id/graph" element={<AppLayout><GraphBuilder /></AppLayout>} />
            <Route path="/projects/:id/agents" element={<AppLayout><EnvironmentSetup /></AppLayout>} />
            <Route path="/projects/:id/simulate" element={<AppLayout><SimulationRunner /></AppLayout>} />
            <Route path="/projects/:id/report" element={<AppLayout><ReportView /></AppLayout>} />
            <Route path="/projects/:id/interact" element={<AppLayout><Interaction /></AppLayout>} />
            <Route path="/graph" element={<AppLayout><GraphBuilder /></AppLayout>} />
            <Route path="/agents" element={<AppLayout><AgentGallery /></AppLayout>} />
            <Route path="/simulation" element={<AppLayout><SimulationRunner /></AppLayout>} />
            <Route path="/reports" element={<AppLayout><ReportView /></AppLayout>} />
            <Route path="/interaction" element={<AppLayout><Interaction /></AppLayout>} />
            <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </BrowserRouter>
      </LLMProvider>
    </ThemeProvider>
  )
}
