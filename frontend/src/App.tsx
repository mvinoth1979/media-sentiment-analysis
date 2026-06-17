import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./lib/supabase";
import { Overview } from "./pages/Overview";
import { Login } from "./pages/Login";
import { BrandSearch } from "./pages/BrandSearch";
import { SourceBreakdown } from "./pages/SourceBreakdown";
import { TopicsView } from "./pages/TopicsView";
import { UserManagement } from "./pages/UserManagement";

type Tab = "overview" | "sources" | "topics" | "users";

const ADMIN_ROLES = new Set(["master_admin", "agency_admin"]);

function App() {
  const [session, setSession]   = useState<Session | null | undefined>(undefined);
  const [brand, setBrand]       = useState<{ id: string; name: string } | null>(null);
  const [tab, setTab]           = useState<Tab>("overview");
  const [isAdmin, setIsAdmin]         = useState(false);
  const [isMasterAdmin, setIsMasterAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, s) => {
      setSession(s);
      if (!s) { setBrand(null); setIsAdmin(false); setIsMasterAdmin(false); setUserEmail(""); }
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!session) return;
    setUserEmail(session.user.email ?? "");
    fetch(
      `${import.meta.env.VITE_SUPABASE_URL}/rest/v1/user_roles?select=role&user_id=eq.${session.user.id}`,
      {
        headers: {
          apikey: import.meta.env.VITE_SUPABASE_ANON_KEY as string,
          Authorization: `Bearer ${session.access_token}`,
        },
      }
    )
      .then(r => r.json())
      .then((rows: { role: string }[]) => {
        const validRows = Array.isArray(rows) ? rows : [];
        setIsAdmin(validRows.some(r => ADMIN_ROLES.has(r.role)));
        setIsMasterAdmin(validRows.some(r => r.role === "master_admin"));
      })
      .catch(() => {});
  }, [session]);

  if (session === undefined) return null;
  if (!session) return <Login />;
  if (!brand) return (
    <BrandSearch
      isAdmin={isAdmin}
      isMasterAdmin={isMasterAdmin}
      onSelect={(id, name) => { setBrand({ id, name }); setTab("overview"); }}
    />
  );

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <h1 className="text-base sm:text-lg font-bold text-indigo-400 shrink-0">MediaSense</h1>
          <button
            onClick={() => setBrand(null)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1 truncate"
          >
            <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="truncate">{brand.name}</span>
          </button>
          <nav className="flex items-center gap-1 ml-2 sm:ml-4 shrink-0">
            <button
              onClick={() => setTab("overview")}
              className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
                tab === "overview" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setTab("sources")}
              className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
                tab === "sources" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Sources
            </button>
            <button
              onClick={() => setTab("topics")}
              className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
                tab === "topics" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Topics
            </button>
            {isAdmin && (
              <button
                onClick={() => setTab("users")}
                className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
                  tab === "users" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Users
              </button>
            )}
          </nav>
        </div>
        <button
          onClick={() => supabase.auth.signOut()}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors shrink-0"
        >
          Sign out
        </button>
      </header>
      <main className="max-w-screen-2xl mx-auto">
        {tab === "overview" && (
          <Overview
            brandId={brand.id}
            brandName={brand.name}
            isAdmin={isAdmin}
            userEmail={userEmail}
          />
        )}
        {tab === "sources" && <SourceBreakdown brandId={brand.id} />}
        {tab === "topics"  && <TopicsView brandId={brand.id} />}
        {tab === "users"   && isAdmin && (
          <UserManagement brandId={brand.id} brandName={brand.name} />
        )}
      </main>
    </div>
  );
}

export default App;
