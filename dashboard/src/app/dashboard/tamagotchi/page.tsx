"use client";
import React from 'react';
import Sidebar from '@/components/Sidebar';
import GlassCard from '@/components/GlassCard';

export default function TamagotchiPage() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
      <Sidebar />
      <main style={{ marginLeft: "300px", padding: "4rem 2rem 2rem", width: "100%" }}>
        <h1 className="accent-text">Tamagotchi Station</h1>
        <div style={{ marginTop: "2rem" }}>
          <GlassCard>
            <p>Your pet is currently sleeping. Check back soon!</p>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}
