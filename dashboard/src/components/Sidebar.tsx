"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

const Sidebar = () => {
  const { data: session } = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [guilds, setGuilds] = useState<any[]>([]);
  const currentGuildId = searchParams.get('guild');

  // Fetch your servers from Discord
    useEffect(() => {
    if (!(session as any)?.accessToken) return;

    // Run both fetches at the same time
    Promise.all([
      fetch('https://discord.com/api/users/@me/guilds', {
        headers: { Authorization: `Bearer ${(session as any).accessToken}` }
      }).then(res => res.json()),
      fetch('http://localhost:8000/api/bot/guilds').then(res => res.json())
    ])
    .then(([userGuilds, botGuildIds]) => {
      if (Array.isArray(userGuilds) && Array.isArray(botGuildIds)) {
        // Only keep guilds that are in BOTH lists
        const filtered = userGuilds.filter(g => botGuildIds.includes(g.id));
        setGuilds(filtered);
      }
    })
    .catch(console.error);
  }, [session]);


  const selectedGuild = guilds.find(g => g.id === currentGuildId);
  // Check if user is Admin (Permission 0x8 is Administrator)
  const isAdmin = selectedGuild ? (BigInt(selectedGuild.permissions) & BigInt(0x8)) !== BigInt(0) : false;

  const selectGuild = (id: string) => {
    router.push(`${pathname}?guild=${id}`);
  };

  return (
    <aside className="glass-card" style={{ 
      width: "280px", height: "calc(100vh - 4rem)", position: "fixed", 
      left: "2rem", top: "2rem", display: "flex", flexDirection: "column", 
      padding: "1.5rem", zIndex: 100 
    }}>
      <h2 className="accent-text" style={{ fontSize: "1.2rem", marginBottom: "2rem" }}>UtilityBot</h2>

      {/* Server Selector Dropdown */}
      <div style={{ marginBottom: "2rem" }}>
        <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.5rem", textTransform: "uppercase" }}>Select Server</p>
        <select 
          value={currentGuildId || ''} 
          onChange={(e) => selectGuild(e.target.value)}
          style={{ width: "100%", padding: "0.8rem", background: "rgba(255,255,255,0.05)", border: "1px solid var(--card-border)", borderRadius: "8px", color: "white" }}
        >
          <option value="">Choose a server...</option>
          {guilds.map(guild => (
            <option key={guild.id} value={guild.id}>{guild.name}</option>
          ))}
        </select>
      </div>

      <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem", flex: 1 }}>
        <Link href={`/dashboard?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard' ? 'active' : ''}`}>
          Overview
        </Link>
        <Link href={`/dashboard/stats?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard/stats' ? 'active' : ''}`}>
          Leaderboards
        </Link>
        <Link href={`/dashboard/tamagotchi?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard/tamagotchi' ? 'active' : ''}`}>
          Tamagotchi
        </Link>
        
        {/* Settings only clickable if Admin */}
        {isAdmin ? (
          <Link href={`/dashboard/settings?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard/settings' ? 'active' : ''}`}>
            Server Settings
          </Link>
        ) : (
          <div className="nav-item locked" style={{ opacity: 0.5, cursor: "not-allowed" }}>
            Server Settings 🔒
          </div>
        )}
      </nav>

      {/* User Info Section */}
      <div style={{ borderTop: "1px solid var(--card-border)", paddingTop: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
          {session?.user?.image && (
  <img src={session.user.image} style={{ width: "35px", height: "35px", borderRadius: "50%" }} />
)}

          <div style={{ overflow: "hidden" }}>
            <p style={{ fontSize: "0.85rem", fontWeight: 600 }}>{session?.user?.name}</p>
            <button onClick={() => signOut()} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "0.7rem", cursor: "pointer" }}>Sign Out</button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .nav-item { padding: 0.8rem 1rem; border-radius: 10px; color: var(--text-muted); text-decoration: none; transition: 0.2s; }
        .nav-item:hover:not(.locked) { background: rgba(255,255,255,0.05); color: white; }
        .nav-item.active { background: rgba(139, 92, 246, 0.1); color: var(--accent); border-left: 3px solid var(--accent); }
      `}</style>
    </aside>
  );
};

export default Sidebar;
