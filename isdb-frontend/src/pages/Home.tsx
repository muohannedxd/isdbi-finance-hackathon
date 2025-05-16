import { useContext } from "react";
import { ScrollToTop } from "@/components/ScrollToTop";
import Layout from "@/components/layout/Layout";
import DashboardSection from "@/components/dashboard/DashboardSection";
import UseCaseSection from "@/components/dashboard/UseCaseSection";
import ReverseTransactionSection from "@/components/dashboard/ReverseTransactionSection";
import CustomSection from "@/components/dashboard/CustomSection";
import { DashboardContext } from "@/lib/context";

export default function Home() {
  const { activeSection } = useContext(DashboardContext);

  const renderContent = () => {
    switch (activeSection) {
      case "dashboard":
        return <DashboardSection />;
      case "use-case":
        return <UseCaseSection />;
      case "reverse-transaction":
        return <ReverseTransactionSection />;
      case "custom":
        return <CustomSection />;
      case "lesson":
        return <div>Lesson</div>;
      default:
        return <DashboardSection />;
    }
  };

  return (
    <>
      <Layout>
        {renderContent()}
      </Layout>
      <ScrollToTop />
    </>
  );
}
