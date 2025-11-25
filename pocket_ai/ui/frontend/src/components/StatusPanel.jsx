import React from 'react';
import { Wifi, Shield, Server, Database } from 'lucide-react';

function StatusPanel({ config }) {
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">System Status</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Profile Card */}
                <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
                    <div className="flex items-center space-x-3 mb-4">
                        <Shield className="text-green-400" />
                        <h3 className="text-lg font-semibold text-white">Security Profile</h3>
                    </div>
                    <div className="text-3xl font-mono text-blue-400 mb-2">
                        {config?.profile || 'UNKNOWN'}
                    </div>
                    <p className="text-slate-400 text-sm">
                        {config?.profile === 'OFFLINE_ONLY'
                            ? 'Strict offline mode. No cloud calls allowed.'
                            : 'Hybrid mode. Cloud calls allowed per policy.'}
                    </p>
                </div>

                {/* Connectivity */}
                <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
                    <div className="flex items-center space-x-3 mb-4">
                        <Wifi className="text-blue-400" />
                        <h3 className="text-lg font-semibold text-white">Connectivity</h3>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span className="text-white">Connected</span>
                    </div>
                </div>
            </div>

            {/* Routing Matrix */}
            <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
                <div className="flex items-center space-x-3 mb-4">
                    <Server className="text-purple-400" />
                    <h3 className="text-lg font-semibold text-white">App Routing</h3>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    {config?.routing && Object.entries(config.routing).map(([key, value]) => (
                        <div key={key} className="flex justify-between border-b border-slate-800 pb-2">
                            <span className="text-slate-400">{key.replace('default_', '').replace('_app', '')}</span>
                            <span className="text-white font-mono">{value}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default StatusPanel;
