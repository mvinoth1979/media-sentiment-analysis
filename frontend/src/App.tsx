import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./lib/supabase";
import { Overview } from "./pages/Overview";
import { Login } from "./pages/Login";
import { BrandSearch } from "./pages/BrandSearch";
import { SourceBreakdown } from "./pages/SourceBreakdown";
import { TopicsView } from "./pages/TopicsView";
import { UserManagement } from "./pages/UserManagement";
import { JournalistCoverage } from "./pages/JournalistCoverage";
import { MentionsMonitor } from "./pages/MentionsMonitor";
import { BrandConfig } from "./pages/BrandConfig";
import { ReviewQueue } from "./pages/ReviewQueue";
import { Sidebar } from "./components/Sidebar";
import type { Tab } from "./components/Sidebar";

const ADMIN_ROLES = new Set(["master_admin", "agency_admin"]);

function App() {
  const [session, setSession]         = useState<Session | null | undefined>(undefined);
  const [brand, setBrand]             = useState<{ id: string; name: string } | null>(null);
  const [tab, setTab]                 = useState<Tab>("overview");
  const [isAdmin, setIsAdmin]         = useState(false);
  const [isMasterAdmin, setIsMasterAdmin] = useState(false);
  const [userEmail, setUserEmail]     = useState("");
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  // Date range — single source of truth, passed to Sidebar (display) + Overview (query)
  const [days, setDays]               = useState(7);
  const [customFrom, setCustomFrom]   = useState("");
  const [customTo, setCustomTo]       = useState("");
  const [showCustom, setShowCustom]   = useState(false);

  function handleDaysChange(d: number) { setDays(d); setShowCustom(false); }
  function handleCustomToggle() { setShowCustom(v => !v); }

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
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar
        brand={brand}
        activeTab={tab}
        onTabChange={setTab}
        onBrandChange={() => setBrand(null)}
        isAdmin={isAdmin}
        lastUpdated={lastUpdated}
        days={days}
        customFrom={customFrom}
        customTo={customTo}
        showCustom={showCustom}
        onDaysChange={handleDaysChange}
        onCustomFromChange={setCustomFrom}
        onCustomToChange={setCustomTo}
        onCustomToggle={handleCustomToggle}
      />

      <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between px-5 py-2.5 bg-white border-b border-gray-200 flex-none">
          <div className="text-xs text-gray-500">
            Signed in as <span className="font-medium text-gray-700">{userEmail}</span>
          </div>
          <button
            onClick={() => supabase.auth.signOut()}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Sign out
          </button>
        </div>

        <div className={`flex-1 min-h-0 ${tab === "overview" ? "overflow-hidden" : "overflow-auto"}`}>
          {tab === "overview" && (
            <Overview
              brandId={brand.id}
              brandName={brand.name}
              isAdmin={isAdmin}
              userEmail={userEmail}
              onLastUpdated={setLastUpdated}
              days={days}
              customFrom={customFrom}
              customTo={customTo}
              showCustom={showCustom}
              onDaysChange={handleDaysChange}
              onCustomFromChange={setCustomFrom}
              onCustomToChange={setCustomTo}
              onCustomToggle={handleCustomToggle}
            />
          )}
          {tab === "sources"     && <SourceBreakdown brandId={brand.id} />}
          {tab === "topics"      && <TopicsView brandId={brand.id} />}
          {tab === "journalists"      && <JournalistCoverage brandId={brand.id} brandName={brand.name} />}
          {tab === "mentions-monitor" && <MentionsMonitor brandId={brand.id} brandName={brand.name} />}
          {tab === "brand-config" && isAdmin && (
            <BrandConfig brandId={brand.id} brandName={brand.name} />
          )}
          {tab === "review-queue" && isAdmin && (
            <ReviewQueue brandId={brand.id} brandName={brand.name} />
          )}
          {tab === "users"       && isAdmin && (
            <UserManagement brandId={brand.id} brandName={brand.name} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
