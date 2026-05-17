import React, { useState, useEffect, useRef } from 'react';
import { 
  Plus, 
  Database, 
  Lightbulb, 
  History, 
  ShieldCheck, 
  FileText, 
  HelpCircle, 
  LogOut, 
  MessageSquare,
  AlertTriangle,
  Bell,
  Settings,
  Paperclip,
  Mic,
  SendHorizontal,
  Bot
} from 'lucide-react';

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    const currentQuery = query;
    setQuery('');
    setLoading(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery }),
      });
      
      const data = await response.json();
      
      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        metrics: data.metrics,
        source: data.source
      };
      
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Sorry, I'm having trouble connecting to the backend. Please ensure the API is running." 
      }]);
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

        <button className="flex items-center justify-center gap-2 bg-mint text-black font-bold py-3 rounded-xl mb-6 hover:bg-mint/90 transition-all">
          <Plus className="w-5 h-5" />
          New Analysis
        </button>

        <nav className="flex-1 space-y-1">
          <NavItem icon={<Database className="w-5 h-5" />} label="Knowledge Base" active />
          <NavItem icon={<Lightbulb className="w-5 h-5" />} label="Example Queries" />
          <NavItem icon={<History className="w-5 h-5" />} label="Recent Sessions" />
          <NavItem icon={<ShieldCheck className="w-5 h-5" />} label="Compliance Logs" />
          <NavItem icon={<FileText className="w-5 h-5" />} label="Documentation" />
        </nav>

        <div className="pt-4 border-t border-white/10 space-y-1">
          <NavItem icon={<HelpCircle className="w-5 h-5" />} label="Support" />
          <NavItem icon={<LogOut className="w-5 h-5" />} label="Sign Out" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Navbar */}
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
              <span className="text-[10px] font-bold text-yellow-500 tracking-wider">FACTS-ONLY MODE ACTIVE</span>
            </div>
            <Bell className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
            <Settings className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
            <HelpCircle className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
            <div className="w-8 h-8 rounded-full bg-mint/20 border border-mint/40 overflow-hidden">
               <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="avatar" />
            </div>
          </div>
        </header>

        {/* Chat Area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
               <Bot className="w-16 h-16 mb-4 text-mint" />
               <h3 className="text-xl font-bold">How can I help you today?</h3>
               <p className="max-w-md">Ask about mutual fund expense ratios, exit loads, or manager details.</p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'user' ? (
                <div className="bg-userBubble border border-mint/20 px-6 py-3 rounded-2xl max-w-xl text-mint">
                  {msg.content}
                </div>
              ) : (
                <div className="bg-card border border-white/5 rounded-2xl p-6 max-w-2xl w-full">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="bg-mint/20 p-1.5 rounded-md">
                      <Bot className="w-4 h-4 text-mint" />
                    </div>
                    <span className="text-xs font-bold text-mint uppercase tracking-widest">Analysis Core</span>
                  </div>
                  
                  <p className="text-sm text-white/80 leading-relaxed mb-6">
                    {msg.content}
                  </p>

                  {msg.metrics && Object.keys(msg.metrics).length > 0 && (
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      {Object.entries(msg.metrics).map(([key, val]) => (
                        <div key={key} className="bg-background/50 border border-white/5 p-4 rounded-xl">
                          <span className="text-[10px] text-white/40 uppercase block mb-1">{key}</span>
                          <span className="text-xl font-bold text-mint">{val}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.source && (
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2 text-[10px] text-white/40">
                        <FileText className="w-3 h-3" />
                        <span>Source: <a href={msg.source.url} target="_blank" className="hover:text-mint transition-colors">{msg.source.fund_name}</a></span>
                      </div>
                      <span className="text-[10px] text-white/20">Updated: {msg.source.last_updated}</span>
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
                      <div className="w-2 h-2 bg-mint rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                      <div className="w-2 h-2 bg-mint rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-2 h-2 bg-mint rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
                   </div>
                </div>
             </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-8 pt-0">
          <form onSubmit={handleSend} className="glass-morphism rounded-2xl p-2 flex items-center gap-2 shadow-2xl">
            <button type="button" className="p-3 text-white/40 hover:text-white transition-colors">
              <Paperclip className="w-5 h-5" />
            </button>
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about expense ratios, fund performance, or compliance..."
              className="flex-1 bg-transparent border-none outline-none text-sm px-2 text-white placeholder:text-white/20"
            />
            <button type="button" className="p-3 text-white/40 hover:text-white transition-colors">
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
    <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${active ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'}`}>
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}

export default App;
