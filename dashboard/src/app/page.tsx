"use client";

import Link from "next/link";
import { signIn, useSession } from "next-auth/react";

export default function Home() {
  const { data: session, status } = useSession();

  return (
    <main style={{ 
      padding: "2rem", 
      display: "flex", 
      flexDirection: "column", 
      alignItems: "center", 
      justifyContent: "center", 
      minHeight: "100vh",
      textAlign: "center"
    }}>
      <div className="animate-fade-in" style={{ maxWidth: "800px" }}>
        <h1 className="accent-text" style={{ fontSize: "4rem", marginBottom: "1rem" }}>
          UtilityBot Dashboard
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.25rem", marginBottom: "2.5rem" }}>
          The all-in-one command center for your Discord community. 
          Manage stats, pets, and server settings with a premium touch.
        </p>
        
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
          {status === "authenticated" ? (
            <Link href="/dashboard" className="btn-primary">
              Enter Dashboard
            </Link>
          ) : (
            <button 
              onClick={() => signIn("discord")} 
              className="btn-primary"
            >
              Login with Discord
            </button>
          )}
          
          <a href="https://discord.com" target="_blank" className="glass-card" style={{ padding: "0.8rem 1.5rem", borderRadius: "12px", border: "1px solid var(--card-border)" }}>
            Add to Discord
          </a>
        </div>
      </div>

      {/* Feature Cards */}
      <div style={{ 
        marginTop: "5rem", 
        display: "grid", 
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
        gap: "2rem", 
        width: "100%", 
        maxWidth: "1000px" 
      }}>
        <div className="glass-card" style={{ padding: "1.5rem" }}>
          <h3 style={{ color: "var(--accent)", fontSize: "1.5rem" }}>5,000+</h3>
          <p style={{ color: "var(--text-muted)" }}>Active Users</p>
        </div>
        <div className="glass-card" style={{ padding: "1.5rem" }}>
          <h3 style={{ color: "var(--accent)", fontSize: "1.5rem" }}>120+</h3>
          <p style={{ color: "var(--text-muted)" }}>Guilds Managed</p>
        </div>
        <div className="glass-card" style={{ padding: "1.5rem" }}>
          <h3 style={{ color: "var(--accent)", fontSize: "1.5rem" }}>1M+</h3>
          <p style={{ color: "var(--text-muted)" }}>Commands Run</p>
        </div>
      </div>
    </main>
  );
}
