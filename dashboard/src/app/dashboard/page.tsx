"use client";

import React, { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import Sidebar from '@/components/Sidebar';
import GlassCard from '@/components/GlassCard';

export default function DashboardPage() {
  const { data: session } = useSession();
  const [userData, setUserData] = useState<any>(null);

  useEffect(() => {
    // Only fetch if we have a logged in user ID
    if (!(session?.user as any)?.id) return;

    const GUILD_ID = "123456789"; // Replace with your test server ID if you have one
    const USER_ID = (session?.user as any)?.id;

    fetch(`http://localhost:8000/api/user/${GUILD_ID}/${USER_ID}`)
      .then(res => res.json())
      .then(data => {
        setUserData(data);
      })
      .catch(err => {
        console.error("Fetch failed:", err);
        // Backup mock data
        setUserData({
          xp: 0, level: 1, balance: 0,
          pet: { name: "None", satiety: 0, energy: 0 },
          tasks: []
        });
      });
  }, [session]);

  if (!userData) {
    return (
      <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
        <Sidebar />
        <main style={{ marginLeft: "300px", padding: "4rem 2rem 2rem", color: "white" }}>
          Searching for your stats...
        </main>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
      <Sidebar />
      <main style={{ marginLeft: "300px", padding: "4rem 2rem 2rem", width: "100%" }}>
        <header style={{ marginBottom: "3rem" }}>
          <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>
            Welcome back, <span className="accent-text">{session?.user?.name}</span>
          </h1>
          <p style={{ color: "var(--text-muted)" }}>Here's what's happening with your bot ecosystem today.</p>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "2rem", marginBottom: "2rem" }}>
          <GlassCard>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>Total XP</p>
            <h2 style={{ fontSize: "2rem" }}>{userData.xp?.toLocaleString()}</h2>
            <p style={{ fontSize: "0.8rem", color: "var(--accent)", marginTop: "0.5rem" }}>Level {userData.level}</p>
          </GlassCard>

          <GlassCard>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>Economy Balance</p>
            <h2 style={{ fontSize: "2rem" }}>${userData.balance?.toLocaleString()}</h2>
          </GlassCard>

          <GlassCard>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>Pet Status</p>
            <h2 style={{ fontSize: "1.5rem" }}>{userData.pet?.name || "No Pet Found"}</h2>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}
