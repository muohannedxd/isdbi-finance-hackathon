import { useContext, useEffect } from "react";
import { LayoutDashboard, MessageSquare, RotateCcw, ChevronLeft, ChevronRight } from "lucide-react";
import { DashboardContext } from "@/lib/context";
import { cn } from "@/lib/utils";
import { useMediaQuery } from "@/lib/hooks";
import ISDB from "@/assets/images/isdb.png";

export default function Sidebar() {
  const { activeSection, setActiveSection, isSidebarCollapsed, setIsSidebarCollapsed } = useContext(DashboardContext);
  const isMobile = useMediaQuery("(max-width: 768px)"); // md breakpoint

  // Auto collapse sidebar on mobile screens
  useEffect(() => {
    if (isMobile) {
      setIsSidebarCollapsed(true);
    }
  }, [isMobile, setIsSidebarCollapsed]);

  const navItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard className="h-5 w-5" />,
    },
    {
      id: "use-case",
      label: "Use Case",
      icon: <MessageSquare className="h-5 w-5" />,
    },
    {
      id: "reverse-transaction",
      label: "Reverse Transaction",
      icon: <RotateCcw className="h-5 w-5" />,
    }
  ];

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <div 
      className={cn(
        "h-full bg-green-50 border-r transition-all duration-300 ease-in-out flex flex-col",
        isSidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className={cn(
        "p-4 flex items-center", 
        isSidebarCollapsed ? "justify-center" : "justify-between"
      )}>
        {!isSidebarCollapsed && (
          <img src={ISDB} className="w-[50%] text-green-800 transition-opacity duration-300" />
        )}
        <button 
          onClick={toggleSidebar}
          className={cn(
            "p-1.5 rounded-full bg-green-100 text-green-800 hover:bg-green-200 transition-colors",
            isSidebarCollapsed ? "mx-auto" : ""
          )}
        >
          {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      
      <nav className="mt-6 flex-1">
        <ul>
          {navItems.map((item) => (
            <li key={item.id} className="mb-2 px-2">
              <button
                className={cn(
                  "flex items-center rounded-lg transition-all duration-200 p-3",
                  isSidebarCollapsed ? "justify-center" : "w-full text-left",
                  activeSection === item.id
                    ? "bg-green-600 text-white"
                    : "hover:bg-green-100 text-green-800"
                )}
                onClick={() => setActiveSection(item.id)}
                title={isSidebarCollapsed ? item.label : undefined}
              >
                <span className={cn("flex-shrink-0", isSidebarCollapsed ? "" : "mr-3")}>{item.icon}</span>
                <span 
                  className={cn(
                    "whitespace-nowrap overflow-hidden transition-all duration-300", 
                    isSidebarCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
                  )}
                >
                  {item.label}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}