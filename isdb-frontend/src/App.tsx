import "@/assets/CSS/App.css";
import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import NoMatch from "./pages/NoMatch";
import { useState, useEffect } from "react";
import { DashboardContext } from "./lib/context";

function App() {
  const [activeSection, setActiveSection] = useState(() => {
    // Get saved section from localStorage or default to "dashboard"
    return localStorage.getItem("activeSection") || "dashboard";
  });
  
  // Save activeSection to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("activeSection", activeSection);
  }, [activeSection]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <DashboardContext.Provider value={{ 
      activeSection, 
      setActiveSection,
      isSidebarCollapsed,
      setIsSidebarCollapsed
    }}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="*" element={<NoMatch />} />
      </Routes>
    </DashboardContext.Provider>
  );
}

export default App;
