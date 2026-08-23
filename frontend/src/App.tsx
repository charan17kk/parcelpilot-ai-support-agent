import { useEffect } from "react";

import { LoginPage } from "./pages/LoginPage";
import { ChatPage } from "./pages/ChatPage";
import { useAuthStore } from "./store/auth";

export default function App() {
  const { user, loading, restore } = useAuthStore();
  useEffect(() => { void restore(); }, [restore]);
  if (loading) return <div className="app-loading"><span className="assistant-orb pulse" /> Loading ParcelPilot Assist…</div>;
  return user ? <ChatPage /> : <LoginPage />;
}
