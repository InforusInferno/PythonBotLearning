"use client";
import React from 'react';
import Sidebar from '@/components/Sidebar';
import GlassCard from '@/components/GlassCard';

export default function SettingsPage() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
      <Sidebar />
      <main style={{ marginLeft: "300px", padding: "4rem 2rem 2rem", width: "100%" }}>
        <h1 className="accent-text">Server Settings</h1>
        <div style={{ marginTop: "2rem" }}>
          <GlassCard>
            <p>Admin permissions required to view settings.</p>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}
