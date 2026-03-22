import { useState } from "react";

// ─── TypeScript Types (unchanged) ───────────────────────────────────────────
type ApiResponse = {
  emotion: string;
  body_state: string;
  action: string;
};

// ─── Helper: Result Row ───────────────────────────────────────────────────────
function ResultRow({
  icon,
  label,
  value,
}: {
  icon: string;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-white/5 border border-white/10">
      <span className="text-xl mt-0.5">{icon}</span>
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-purple-300 mb-0.5">
          {label}
        </p>
        <p className="text-white/90 font-medium leading-snug">{value}</p>
      </div>
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────────────────────
function App() {
  const [message, setMessage] = useState<string>("");
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  // API call logic — unchanged
  const handleAnalyze = async () => {
    if (!message.trim()) {
      setError("Please describe how you're feeling first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Something went wrong");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || "Error occurred. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  // Allow Ctrl+Enter / Cmd+Enter to submit
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      handleAnalyze();
    }
  };

  return (
    // ── Full-screen gradient background ──────────────────────────────────────
    <div className="min-h-screen w-full bg-gradient-to-br from-[#0f172a] via-[#1e1b4b] to-[#312e81] flex items-center justify-center px-4 py-12">

      {/* Ambient glow blobs for depth */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-purple-700/20 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-blue-700/20 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-indigo-900/10 blur-3xl" />
      </div>

      {/* ── Centered content container ──────────────────────────────────── */}
      <div className="relative z-10 w-full max-w-xl flex flex-col gap-6">

        {/* ── App Title ──────────────────────────────────────────────────── */}
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight bg-gradient-to-r from-purple-300 via-fuchsia-200 to-blue-300 bg-clip-text text-transparent mb-2">
            InnerEase AI
          </h1>
          <p className="text-white/40 text-sm font-light tracking-wide">
            Understand your nervous system • Find calm
          </p>
        </div>

        {/* ── Input Glass Card ────────────────────────────────────────────── */}
        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-2xl shadow-black/30 transition-all duration-300">
          <label className="block text-white/60 text-xs font-semibold uppercase tracking-widest mb-3">
            How are you feeling right now?
          </label>

          <textarea
            id="feeling-input"
            className="w-full resize-none rounded-xl bg-white/5 border border-white/10 text-white/90 placeholder-white/25 p-4 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500/60 focus:border-purple-500/40 transition-all duration-200"
            rows={4}
            placeholder="Describe what's happening in your body and mind… e.g. 'I feel tightness in my chest and my thoughts are racing.'"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
          />

          <p className="text-white/20 text-xs mt-1 mb-4">
            Tip: press <kbd className="font-mono bg-white/10 px-1 rounded">Ctrl+Enter</kbd> to analyze
          </p>

          <button
            id="analyze-btn"
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full py-3 px-6 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 active:scale-[0.98] transition-all duration-200 shadow-lg shadow-purple-900/40 disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
                Analyzing…
              </span>
            ) : (
              "✦ Analyze My State"
            )}
          </button>
        </div>

        {/* ── Error Message ───────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-400/20 text-red-300 text-sm transition-all duration-300">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* ── Result Glass Card ─────────────────────────────────────────────
            Appears only when a response has been received.
        ────────────────────────────────────────────────────────────────────── */}
        {result && (
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-2xl shadow-black/30 flex flex-col gap-3 transition-all duration-500 animate-fade-in">
            <p className="text-white/50 text-xs font-semibold uppercase tracking-widest mb-1">
              Your Regulation Report
            </p>

            <ResultRow
              icon="💜"
              label="Emotion"
              value={result.emotion}
            />
            <ResultRow
              icon="🫁"
              label="Body State"
              value={result.body_state}
            />
            <ResultRow
              icon="🌿"
              label="Recommended Action"
              value={result.action}
            />
          </div>
        )}

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <p className="text-center text-white/20 text-xs pb-2">
          InnerEase AI · Nervous System Regulation
        </p>
      </div>
    </div>
  );
}

export default App;