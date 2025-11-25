import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, MessageSquare, Settings, Mic } from 'lucide-react';

// Components
import StatusPanel from './components/StatusPanel';
import ChatInterface from './components/ChatInterface';

function App() {
    const [config, setConfig] = useState(null);
    const [activeTab, setActiveTab] = useState('chat');

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        try {
            const res = await axios.get('http://localhost:8000/config');
            setConfig(res.data);
        } catch (err) {
            console.error("Failed to fetch config", err);
        }
    };

    return (
        <div className="min-h-screen flex flex-col md:flex-row">
            {/* Sidebar */}
            <div className="w-full md:w-64 bg-slate-900 p-4 border-r border-slate-800">
                <h1 className="text-2xl font-bold text-blue-400 mb-8">POCKET-AI</h1>

                <nav className="space-y-2">
                    <button
                        onClick={() => setActiveTab('chat')}
                        className={`w-full flex items-center space-x-2 p-3 rounded transition ${activeTab === 'chat' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
                    >
                        <MessageSquare size={20} />
                        <span>Chat</span>
                    </button>

                    <button
                        onClick={() => setActiveTab('status')}
                        className={`w-full flex items-center space-x-2 p-3 rounded transition ${activeTab === 'status' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
                    >
                        <Activity size={20} />
                        <span>Status</span>
                    </button>

                    <button
                        onClick={() => setActiveTab('settings')}
                        className={`w-full flex items-center space-x-2 p-3 rounded transition ${activeTab === 'settings' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
                    >
                        <Settings size={20} />
                        <span>Settings</span>
                    </button>
                </nav>

                <div className="mt-auto pt-8">
                    <div className="bg-slate-800 p-3 rounded text-xs text-slate-400">
                        Profile: <span className="text-white font-mono">{config?.profile || 'Loading...'}</span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 bg-slate-950 p-4 md:p-8 overflow-y-auto">
                {activeTab === 'chat' && <ChatInterface />}
                {activeTab === 'status' && <StatusPanel config={config} />}
                {activeTab === 'settings' && <div className="text-slate-400">Settings not implemented in prototype.</div>}
            </div>
        </div>
    );
}

export default App;
