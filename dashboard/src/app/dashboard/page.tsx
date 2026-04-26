"use client";

import React, { useEffect, useState, Suspense } from 'react';
import { useSession } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import GlassCard from '@/components/GlassCard';

function DashboardContent() {
  const [userData, setUserData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { data: session } = useSession();
  const searchParams = useSearchParams();

  useEffect(() => {
    const guildId = searchParams?.get('guild');
    const userId = (session?.user as any)?.id;

    if (!guildId || !userId) {
      setLoading(false);
      return;
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    fetch(`${API_URL}/api/user/${guildId}/${userId}`)
      .then(res => res.json())
      .then(data => {
        setUserData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch user data:", err);
        setLoading(false);
        // Fallback mock data if API isn't running
        setUserData({
          xp: 1250,
          level: 3,
          balance: 5000,
          pet: { name: "Nebula", satiety: 85, energy: 90, happiness: 100 },
          tasks: [
            { id: 1, content: "Update bot prefix", completed: false },
            { id: 2, content: "Check leaderboard", completed: true }
          ]
        });
      });
  }, []);

  if (loading) return <div style={{ color: "white", padding: "2rem" }}>Loading Nebula Dashboard...</div>;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
      <Sidebar />
      
      <main style={{ marginLeft: "300px", padding: "4rem 2rem 2rem", width: "100%" }}>
        <header style={{ marginBottom: "3rem" }}>
          <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>Welcome back, <span className="accent-text">{session?.user?.name || "User"}</span></h1>
          <p style={{ color: "var(--text-muted)" }}>Here's what's happening with your bot ecosystem today.</p>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "2rem", marginBottom: "2rem" }}>
          <GlassCard>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>Total XP</p>
            <h2 style={{ fontSize: "2rem" }}>{userData?.xp?.toLocaleString()}</h2>
            <div style={{ marginTop: "1rem", height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
              <div style={{ width: "65%", height: "100%", background: "var(--accent)", borderRadius: "2px" }}></div>
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--accent)", marginTop: "0.5rem" }}>Level {userData?.level}</p>
          </GlassCard>

          <GlassCard>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>Economy Balance</p>
            <h2 style={{ fontSize: "2rem" }}>${userData?.balance?.toLocaleString()}</h2>
            <p style={{ fontSize: "0.8rem", color: "var(--success)", marginTop: "0.5rem" }}>+ $250 today</p>
          </GlassCard>

          <GlassCard>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>Tamagotchi Status</p>
            <h2 style={{ fontSize: "1.5rem" }}>{userData?.pet?.name || "No Pet"}</h2>
            <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Hunger</p>
                <div style={{ height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                  <div style={{ width: `${userData?.pet?.satiety}%`, height: "100%", background: "var(--accent)" }}></div>
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Energy</p>
                <div style={{ height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                  <div style={{ width: `${userData?.pet?.energy}%`, height: "100%", background: "var(--accent)" }}></div>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "2rem" }}>
          <GlassCard>
            <h3 style={{ marginBottom: "1.5rem" }}>Active Tasks</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {userData?.tasks?.map((task: any) => (
                <div key={task.id} style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "1rem", 
                  padding: "1rem", 
                  background: "rgba(255,255,255,0.02)", 
                  borderRadius: "12px",
                  border: "1px solid var(--card-border)"
                }}>
                  <input type="checkbox" checked={task.completed} readOnly style={{ accentColor: "var(--accent)" }} />
                  <span style={{ textDecoration: task.completed ? "line-through" : "none", color: task.completed ? "var(--text-muted)" : "white" }}>
                    {task.content}
                  </span>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <h3 style={{ marginBottom: "1.5rem" }}>Quick Actions</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <button className="btn-primary" style={{ width: "100%" }}>Feed Pet</button>
              <button className="glass-card" style={{ width: "100%", padding: "0.8rem", borderRadius: "12px" }}>Play Game</button>
              <button className="glass-card" style={{ width: "100%", padding: "0.8rem", borderRadius: "12px" }}>Clean Pet</button>
            </div>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div style={{ color: "white", padding: "2rem", background: "var(--background)", minHeight: "100vh" }}>Loading Nebula Dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
