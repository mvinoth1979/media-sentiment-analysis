import { Overview } from "./pages/Overview";

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-lg font-bold text-indigo-400">MediaSense</h1>
      </header>
      <main>
        <Overview />
      </main>
    </div>
  );
}

export default App;
