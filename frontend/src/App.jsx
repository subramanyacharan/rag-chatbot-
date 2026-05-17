import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Plus,
  Database,
  Lightbulb,
  History,
  ShieldCheck,
  FileText,
  HelpCircle,
  LogOut,
  AlertTriangle,
  Bell,
  Settings,
  Paperclip,
  Mic,
  SendHorizontal,
  Bot,
  X,
} from 'lucide-react';

function createSession() {
  return {
    id: crypto.randomUUID(),
    title: 'New Analysis',
    messages: [],
    createdAt: Date.now(),
  };
}

function sessionTitleFromQuery(query) {
  const trimmed = query.trim();
  if (!trimmed) return 'New Analysis';
  return trimmed.length > 36 ? `${trimmed.slice(0, 36)}…` : trimmed;
}

function App() {
  const initialSession = useRef(createSession());
  const [sessions, setSessions] = useState([initialSession.current]);
  const [activeSessionId, setActiveSessionId] = useState(initialSession.current.id);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const activeSession =
    sessions.find((s) => s.id === activeSessionId) ?? sessions[0];
  const messages = activeSession?.messages ?? [];

  const updateActiveSession = useCallback((updater, titleFromQuery) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== activeSessionId) return s;
        const nextMessages =
          typeof updater === 'function' ? updater(s.messages) : updater;
        const nextTitle =
          titleFromQuery && s.title === 'New Analysis'
            ? sessionTitleFromQuery(titleFromQuery)
            : s.title;
        return { ...s, messages: nextMessages, title: nextTitle };
      }),
    );
  }, [activeSessionId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, activeSessionId]);

  const getApiUrl = () => {
    const url = import.meta.env.VITE_API_URL?.replace(/\/$/, '');
    if (url) return url;
    if (import.meta.env.DEV) return 'http://localhost:8000';
    return null;
  };

  const handleNewAnalysis = () => {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveSessionId(session.id);
    setQuery('');
  };

  const handleCloseSession = (sessionId, e) => {
    e.stopPropagation();
    setSessions((prev) => {
      if (prev.length === 1) {
        const fresh = createSession();
        setActiveSessionId(fresh.id);
        return [fresh];
      }
      const next = prev.filter((s) => s.id !== sessionId);
      if (activeSessionId === sessionId) {
        setActiveSessionId(next[0].id);
      }
      return next;
    });
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    const currentQuery = query;
    updateActiveSession((prev) => [...prev, userMsg], currentQuery);
    setQuery('');
    setLoading(true);

    const apiUrl = getApiUrl();
    if (!apiUrl) {
      updateActiveSession((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'The assistant is temporarily unavailable. Please try again in a few minutes.',
          isError: true,
          showSource: false,
        },
      ]);
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery }),
      });

      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error(`Invalid response (${response.status})`);
      }

      if (!response.ok) {
        const detail =
          typeof data?.detail === 'string'
            ? data.detail
            : data?.error || 'The service returned an error.';
        throw new Error(detail);
      }

      if (data.error) {
        throw new Error(data.error);
      }

      const failedStatuses = ['error', 'config_error', 'rate_limited'];
      if (failedStatuses.includes(data.status)) {
        updateActiveSession((prev) => [
          ...prev,
          {
            role: 'assistant',
            content:
              data.answer ||
              'The assistant is temporarily unavailable. Please try again in a few minutes.',
            isError: true,
            showSource: false,
          },
        ]);
        return;
      }

      const answer =
        data.answer ?? 'I do not have the information to answer that.';
      if (typeof answer === 'string' && /^Error:/i.test(answer)) {
        updateActiveSession((prev) => [
          ...prev,
          {
            role: 'assistant',
            content:
              'The assistant is temporarily unavailable. Please try again in a few minutes.',
            isError: true,
            showSource: false,
          },
        ]);
        return;
      }

      const showSource =
        data.show_source === true && data.source && data.status === 'success';

      updateActiveSession((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: answer,
          metrics: data.metrics,
          source: showSource ? data.source : null,
          showSource,
          status: data.status,
        },
      ]);
    } catch (err) {
      console.error('Chat request failed:', err);
      const isConfig = !import.meta.env.VITE_API_URL && !import.meta.env.DEV;
      const message = isConfig
        ? 'The assistant is temporarily unavailable. Please try again in a few minutes.'
        : err instanceof Error &&
            err.message &&
            !err.message.includes('Failed to fetch')
          ? err.message
          : 'The assistant is temporarily unavailable. Please try again in a few minutes.';

      updateActiveSession((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: message,
          isError: true,
          showSource: false,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-white font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/10 flex flex-col p-4 bg-[#0B120E]">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="bg-mint/20 p-2 rounded-lg">
            <Database className="w-5 h-5 text-mint" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-mint">RAG Insights</h1>
            <p className="text-[10px] text-white/40">Source: Groww Facts 2026</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleNewAnalysis}
          className="flex items-center justify-center gap-2 bg-mint text-black font-bold py-3 rounded-xl mb-4 hover:bg-mint/90 transition-all"
        >
          <Plus className="w-5 h-5" />
          New Analysis
        </button>

        <div className="mb-4 flex-1 min-h-0 flex flex-col">
          <div className="flex items-center gap-2 px-3 mb-2 text-white/40">
            <History className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">
              Recent Sessions
            </span>
          </div>
          <ul className="space-y-1 overflow-y-auto flex-1 pr-1">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setActiveSessionId(session.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-left transition-all group ${
                    session.id === activeSessionId
                      ? 'bg-white/10 text-white'
                      : 'text-white/40 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <span className="text-sm font-medium truncate flex-1">
                    {session.title}
                  </span>
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => handleCloseSession(session.id, e)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        handleCloseSession(session.id, e);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-white/10 text-white/50 hover:text-white shrink-0"
                    aria-label={`Close ${session.title}`}
                  >
                    <X className="w-3.5 h-3.5" />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <nav className="space-y-1 border-t border-white/10 pt-4">
          <NavItem icon={<Database className="w-5 h-5" />} label="Knowledge Base" active />
          <NavItem icon={<Lightbulb className="w-5 h-5" />} label="Example Queries" />
          <NavItem icon={<ShieldCheck className="w-5 h-5" />} label="Compliance Logs" />
          <NavItem icon={<FileText className="w-5 h-5" />} label="Documentation" />
        </nav>

        <div className="pt-4 border-t border-white/10 space-y-1 mt-4">
          <NavItem icon={<HelpCircle className="w-5 h-5" />} label="Support" />
          <NavItem icon={<LogOut className="w-5 h-5" />} label="Sign Out" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        <header className="h-16 border-b border-white/10 flex items-center justify-between px-8 bg-[#0B120E]/50 backdrop-blur-md z-10">
          <div className="flex items-center gap-8">
            <h2 className="text-xl font-bold text-mint">FundQuest AI</h2>
            <nav className="flex items-center gap-6 text-sm text-white/60">
              <span className="hover:text-white cursor-pointer">Market Data</span>
              <span className="hover:text-white cursor-pointer">Portfolio</span>
              <span className="hover:text-white cursor-pointer">Disclosures</span>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/20 px-4 py-1.5 rounded-full">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              <span className="text-[10px] font-bold text-yellow-500 tracking-wider">
                FACTS-ONLY MODE ACTIVE
              </span>
            </div>
            <Bell className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
            <Settings className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
            <HelpCircle className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
            <div className="w-8 h-8 rounded-full bg-mint/20 border border-mint/40 overflow-hidden">
              <img
                src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"
                alt="avatar"
              />
            </div>
          </div>
        </header>

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth"
        >
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
              <Bot className="w-16 h-16 mb-4 text-mint" />
              <h3 className="text-xl font-bold">How can I help you today?</h3>
              <p className="max-w-md">
                Ask about mutual fund expense ratios, exit loads, or manager details.
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'user' ? (
                <div className="bg-userBubble border border-mint/20 px-6 py-3 rounded-2xl max-w-xl text-mint">
                  {msg.content}
                </div>
              ) : (
                <div
                  className={`bg-card border rounded-2xl p-6 max-w-2xl w-full ${
                    msg.isError ? 'border-red-500/30' : 'border-white/5'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-4">
                    <div className="bg-mint/20 p-1.5 rounded-md">
                      <Bot className="w-4 h-4 text-mint" />
                    </div>
                    <span className="text-xs font-bold text-mint uppercase tracking-widest">
                      Analysis Core
                    </span>
                  </div>

                  <p className="text-sm text-white/80 leading-relaxed mb-6">
                    {msg.content}
                  </p>

                  {msg.metrics && Object.keys(msg.metrics).length > 0 && (
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      {Object.entries(msg.metrics).map(([key, val]) => (
                        val && (
                          <div
                            key={key}
                            className="bg-background/50 border border-white/5 p-4 rounded-xl"
                          >
                            <span className="text-[10px] text-white/40 uppercase block mb-1">
                              {key}
                            </span>
                            <span className="text-xl font-bold text-mint">{val}</span>
                          </div>
                        )
                      ))}
                    </div>
                  )}

                  {msg.showSource && msg.source && (
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2 text-[10px] text-white/40">
                        <FileText className="w-3 h-3" />
                        <span>
                          Source:{' '}
                          <a
                            href={msg.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-mint transition-colors"
                          >
                            {msg.source.fund_name}
                          </a>
                        </span>
                      </div>
                      <span className="text-[10px] text-white/20">
                        Updated: {msg.source.last_updated}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-card border border-white/5 rounded-2xl p-6 w-32 flex items-center justify-center">
                <div className="flex gap-1">
                  <div
                    className="w-2 h-2 bg-mint rounded-full animate-bounce"
                    style={{ animationDelay: '0s' }}
                  />
                  <div
                    className="w-2 h-2 bg-mint rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  />
                  <div
                    className="w-2 h-2 bg-mint rounded-full animate-bounce"
                    style={{ animationDelay: '0.4s' }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="p-8 pt-0">
          <form
            onSubmit={handleSend}
            className="glass-morphism rounded-2xl p-2 flex items-center gap-2 shadow-2xl"
          >
            <button
              type="button"
              className="p-3 text-white/40 hover:text-white transition-colors"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about expense ratios, fund performance, or compliance..."
              className="flex-1 bg-transparent border-none outline-none text-sm px-2 text-white placeholder:text-white/20"
            />
            <button
              type="button"
              className="p-3 text-white/40 hover:text-white transition-colors"
            >
              <Mic className="w-5 h-5" />
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-mint text-black p-3 rounded-xl hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
            >
              <SendHorizontal className="w-5 h-5" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, active = false }) {
  return (
    <div
      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${
        active ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'
      }`}
    >
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}

export default App;
