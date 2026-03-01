"use client"

import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ShieldAlert, Activity, Database, ShieldCheck, Lock } from 'lucide-react';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://your-project.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'your-anon-key';
const supabase = createClient(supabaseUrl, supabaseKey);

export default function Dashboard() {
    const [logs, setLogs] = useState<any[]>([]);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [proofs, setProofs] = useState<any[]>([]);
    const [criticalAlert, setCriticalAlert] = useState<any | null>(null);

    useEffect(() => {
        // Polling for PoC simplicity
        const fetchData = async () => {
            // 1. Fetch Logs
            const { data: rawLogs } = await supabase
                .from('raw_logs')
                .select('*')
                .order('timestamp', { ascending: false })
                .limit(20);
            if (rawLogs) setLogs(rawLogs);

            // 2. Fetch Alerts for Graph
            const { data: incomingAlerts } = await supabase
                .from('alerts')
                .select('*, raw_logs(*)')
                .order('id', { ascending: false })
                .limit(20);

            if (incomingAlerts && incomingAlerts.length > 0) {
                setAlerts([...incomingAlerts].reverse());

                // Check for CRITICAL
                const critical = incomingAlerts.find(a => a.severity === 'CRITICAL');
                if (critical) {
                    setCriticalAlert(critical);
                } else {
                    setCriticalAlert(null);
                }
            }

            // 3. Fetch Blockchain Proofs
            const { data: chainProofs } = await supabase
                .from('blockchain_proofs')
                .select('*, alerts(*)')
                .order('id', { ascending: false })
                .limit(10);
            if (chainProofs) setProofs(chainProofs);
        };

        fetchData();
        const interval = setInterval(fetchData, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-300 p-4 font-mono flex flex-col">
            <header className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                <div className="flex items-center space-x-3">
                    <ShieldCheck className="text-emerald-500 w-8 h-8" />
                    <h1 className="text-2xl font-bold text-white tracking-wider">AUTONOMOUS CYBER DEFENSE</h1>
                </div>
                <div className="text-sm text-slate-500 flex items-center space-x-2">
                    <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </span>
                    <span>SYSTEM ACTIVE</span>
                </div>
            </header>

            {/* Critical Threat Modal */}
            {criticalAlert && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-red-950 border-2 border-red-500 rounded-lg max-w-2xl w-full p-8 shadow-[0_0_50px_rgba(239,68,68,0.4)] animate-pulse">
                        <div className="flex items-center justify-center mb-6">
                            <ShieldAlert className="text-red-500 w-20 h-20 animate-bounce" />
                        </div>
                        <h2 className="text-4xl font-black text-red-500 text-center mb-6 tracking-widest">CRITICAL THREAT ISOLATED</h2>

                        <div className="bg-red-900/50 p-6 rounded border border-red-500/50 mb-6 font-mono">
                            <div className="grid grid-cols-2 gap-4 text-lg">
                                <div className="text-red-300">Target User:</div>
                                <div className="text-white font-bold">{criticalAlert.raw_logs?.user_id || 'UNKNOWN'}</div>

                                <div className="text-red-300">Action Type:</div>
                                <div className="text-white font-bold">{criticalAlert.raw_logs?.action || 'UNKNOWN'}</div>

                                <div className="text-red-300">Math Penalty Score:</div>
                                <div className="text-white font-bold">{criticalAlert.anomaly_score.toFixed(2)}</div>

                                <div className="text-red-300">AI Assessment:</div>
                                <div className="text-red-100 italic col-span-2 text-sm border-t border-red-800 mt-2 pt-2">Reasoning unavailable here.</div>
                            </div>
                        </div>

                        <div className="text-center">
                            <div className="inline-flex items-center space-x-2 bg-red-500 text-white px-6 py-3 rounded font-bold tracking-widest">
                                <Lock className="w-5 h-5" />
                                <span>STATUS: CONNECTION SEVERED</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1">

                {/* PANE 1: STREAM */}
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col">
                    <div className="flex items-center space-x-2 text-indigo-400 mb-4 pb-2 border-b border-slate-800">
                        <Activity className="w-5 h-5" />
                        <h2 className="font-bold tracking-wider">LIVE INGEST STREAM</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto space-y-3 font-mono text-sm max-h-[70vh]">
                        {logs.length === 0 ? <div className="text-slate-500 italic">Waiting for logs...</div> : logs.map(log => (
                            <div key={log.id} className="p-3 bg-slate-950 border border-slate-800 rounded">
                                <div className="text-slate-500 text-xs mb-1">{new Date(log.timestamp).toLocaleTimeString()}</div>
                                <div className="flex justify-between">
                                    <span className="text-indigo-300">{log.user_id}</span>
                                    <span className="text-slate-400">vol: {log.volume}</span>
                                </div>
                                <div className="text-slate-300 mt-1">{log.action}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* PANE 2: THREAT VISUALIZER */}
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col">
                    <div className="flex items-center space-x-2 text-amber-500 mb-4 pb-2 border-b border-slate-800">
                        <Activity className="w-5 h-5" />
                        <h2 className="font-bold tracking-wider">MATH ANOMALY SCORE</h2>
                    </div>
                    <div className="flex-1 min-h-[300px]">
                        {alerts.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-slate-500 italic">No anomaly data yet.</div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={alerts}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis dataKey="id" hide />
                                    <YAxis stroke="#475569" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#020617', borderColor: '#1e293b' }}
                                        labelStyle={{ display: 'none' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="anomaly_score"
                                        stroke="#f59e0b"
                                        strokeWidth={2}
                                        dot={{ fill: '#f59e0b', r: 4 }}
                                        activeDot={{ r: 6 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* PANE 3: THE VAULT */}
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col">
                    <div className="flex items-center space-x-2 text-emerald-500 mb-4 pb-2 border-b border-slate-800">
                        <Database className="w-5 h-5" />
                        <h2 className="font-bold tracking-wider">THE BLOCKCHAIN VAULT</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto space-y-4 max-h-[70vh]">
                        {proofs.length === 0 ? <div className="text-slate-500 italic">Vault is empty...</div> : proofs.map(proof => (
                            <div key={proof.id} className="p-3 bg-slate-950 border border-emerald-900/30 rounded relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-12 h-12 bg-emerald-500/10 rounded-bl-full"></div>

                                <div className="text-xs text-slate-500 mb-2">Immutable Proof Logged</div>

                                <div className="mb-2">
                                    <div className="text-xs text-slate-500">SHA-256 Hash:</div>
                                    <div className="font-mono text-emerald-400 text-[10px] break-all" title={proof.sha256_hash}>
                                        {proof.sha256_hash}
                                    </div>
                                </div>

                                <div>
                                    <div className="text-xs text-slate-500">Local Blockchain Tx:</div>
                                    <div className="font-mono text-indigo-400 text-xs truncate block">
                                        {proof.transaction_id.substring(0, 20)}...
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </div>
    );
}
