import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./lib/supabase";
import { Overview } from "./pages/Overview";
import { Login } from "./pages/Login";
import { BrandSearch } from "./pages/BrandSearch";

function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined);
  const [brand, setBrand] = useState<{ id: string; name: string } | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, s) => {
      setSession(s);
      if (!s) setBrand(null);
    });
    return () => subscription.unsubscribe();
  }, []);

  if (session === undefined) return null;
  if (!session) return <Login />;
  if (!brand) return <BrandSearch onSelect={(id, name) => setBrand({ id, name })} />;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-indigo-400">MediaSense</h1>
          <button
            onClick={() => setBrand(null)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Change brand
          </button>
        </div>
        <button
          onClick={() => supabase.auth.signOut()}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
        >
          Sign out
        </button>
      </header>
      <main>
        <Overview brandId={brand.id} brandName={brand.name} />
      </main>
    </div>
  );
}

export default App;
