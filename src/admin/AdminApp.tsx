import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { getToken } from "./api/client";
import { AdminLayout } from "./layout/AdminLayout";
import { AssistantPage } from "./pages/AssistantPage";
import { ConversationsPage } from "./pages/ConversationsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { LeadsPage } from "./pages/LeadsPage";
import { LoginPage } from "./pages/LoginPage";
import { PricingPage } from "./pages/PricingPage";
import { ServicesPage } from "./pages/ServicesPage";

function RequireAuth() {
  if (!getToken()) {
    return <Navigate to="/admin/login" replace />;
  }
  return <Outlet />;
}

export default function AdminApp() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="conversaciones" element={<ConversationsPage />} />
          <Route path="leads" element={<LeadsPage />} />
          <Route path="conocimiento" element={<KnowledgePage />} />
          <Route path="servicios" element={<ServicesPage />} />
          <Route path="precios" element={<PricingPage />} />
          <Route path="assistant" element={<AssistantPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
