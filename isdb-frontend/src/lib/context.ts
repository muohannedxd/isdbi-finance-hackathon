import { createContext } from 'react';

export type DashboardContextType = {
  activeSection: string;
  setActiveSection: (section: string) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (collapsed: boolean) => void;
};

export const DashboardContext = createContext<DashboardContextType>({
  activeSection: 'dashboard',
  setActiveSection: () => {},
  isSidebarCollapsed: false,
  setIsSidebarCollapsed: () => {},
});