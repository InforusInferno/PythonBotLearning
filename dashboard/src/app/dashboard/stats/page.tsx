"use client";

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import GlassCard from '@/components/GlassCard';
import { useSearchParams } from 'next/navigation';

export default function StatsPage() {
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [type, setType] = useState('xp');
  const [loading, setLoading] = useState(true);
  const searchParams = useSearchParams();
  const guildId = searchParams?.get('guild') || '';

  useEffect(() => {
    const runId = `baseline-${Date.now()}`;
    if (!guildId) {
      // #region agent log
      fetch('http://127.0.0.1:7777/ingest/8cbbb94c-b320-4ef3-906e-10e61b91f1a0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'6bb96e'},body:JSON.stringify({sessionId:'6bb96e',runId,hypothesisId:'H8_NAV_STATE',location:'dashboard/stats/page.tsx:missing-guild',message:'stats page missing guild query',data:{guildId},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      setLeaderboard([]);
      setLoading(false);
      return;
    }
    setLoading(true);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const leaderboardUrl = `${API_URL}/api/leaderboard/${guildId}?type=${type}`;
    // #region agent log
    fetch('http://127.0.0.1:7777/ingest/8cbbb94c-b320-4ef3-906e-10e61b91f1a0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'6bb96e'},body:JSON.stringify({sessionId:'6bb96e',runId,hypothesisId:'H1_API_BASE_URL',location:'dashboard/stats/page.tsx:leaderboard-url',message:'stats page using leaderboard URL',data:{leaderboardUrl,type},timestamp:Date.now()})}).catch(()=>{});
    // #endregion

    fetch(leaderboardUrl)
      .then(res => {
        // #region agent log
        fetch('http://127.0.0.1:7777/ingest/8cbbb94c-b320-4ef3-906e-10e61b91f1a0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'6bb96e'},body:JSON.stringify({sessionId:'6bb96e',runId,hypothesisId:'H3_ROUTE_OR_STATUS',location:'dashboard/stats/page.tsx:leaderboard-status',message:'leaderboard fetch returned status',data:{status:res.status,ok:res.ok,url:res.url},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        return res.json();
      })
      .then(data => {
        setLeaderboard(data);
        setLoading(false);
      })
      .catch((err) => {
        // #region agent log
        fetch('http://127.0.0.1:7777/ingest/8cbbb94c-b320-4ef3-906e-10e61b91f1a0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'6bb96e'},body:JSON.stringify({sessionId:'6bb96e',runId,hypothesisId:'H2_CORS_OR_NETWORK',location:'dashboard/stats/page.tsx:leaderboard-error',message:'leaderboard fetch failed',data:{error:String(err)},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        // Mock data if API is down
        setLeaderboard([
          { user_id: "User1", xp: 5000, balance: 10000 },
          { user_id: "User2", xp: 4500, balance: 8000 },
          { user_id: "User3", xp: 3000, balance: 5000 },
        ]);
        setLoading(false);
      });
  }, [type, guildId]);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
      <Sidebar />
      <main style={{ marginLeft: "300px", padding: "4rem 2rem 2rem", width: "100%" }}>
        <header style={{ marginBottom: "3rem" }}>
          <h1 style={{ fontSize: "2.5rem" }}>Global <span className="accent-text">Leaderboards</span></h1>
          <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
            <button 
              onClick={() => setType('xp')}
              className={type === 'xp' ? "btn-primary" : "glass-card"}
              style={{ padding: "0.5rem 1.5rem", borderRadius: "8px" }}
            >
              XP Rankings
            </button>
            <button 
              onClick={() => setType('economy')}
              className={type === 'economy' ? "btn-primary" : "glass-card"}
              style={{ padding: "0.5rem 1.5rem", borderRadius: "8px" }}
            >
              Economy Rankings
            </button>
          </div>
        </header>

        <GlassCard>
          {loading ? <p>Loading rankings...</p> : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid var(--card-border)", color: "var(--text-muted)" }}>
                  <th style={{ padding: "1rem" }}>Rank</th>
                  <th style={{ padding: "1rem" }}>User ID</th>
                  <th style={{ padding: "1rem" }}>{type === 'xp' ? "XP" : "Balance"}</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((user, index) => (
                  <tr key={user.user_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.02)" }}>
                    <td style={{ padding: "1rem", fontWeight: 800 }}>#{index + 1}</td>
                    <td style={{ padding: "1rem" }}>{user.user_id}</td>
                    <td style={{ padding: "1rem", color: "var(--accent)" }}>
                      {type === 'xp' ? user.xp?.toLocaleString() : `$${user.balance?.toLocaleString()}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </GlassCard>
      </main>
    </div>
  );
}
