import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

const SidebarContent = () => {
  const { data: session } = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [guilds, setGuilds] = useState<any[]>([]);
  const currentGuildId = searchParams?.get('guild') || '';

  // Fetch both Discord guilds and bot guilds, then intersect
  useEffect(() => {
    if (!(session as any)?.accessToken) return;

    // 1️⃣ Fetch Discord guilds (full list)
    fetch('https://discord.com/api/users/@me/guilds', {
      headers: { Authorization: `Bearer ${(session as any).accessToken}` }
    })
      .then(r => r.json())
      .then((userGuilds: any[]) => {
        // 2️⃣ Fetch bot's guild IDs
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        fetch(`${API_URL}/api/bot/guilds`)
          .then(r => r.json())
          .then((botIds: string[]) => {
            const safeUserGuilds = Array.isArray(userGuilds) ? userGuilds : [];
            const safeBotIds = Array.isArray(botIds) ? botIds : [];
            const intersect = safeUserGuilds.filter(g => safeBotIds.includes(g.id));
            setGuilds(intersect);
          })
          .catch(console.error);
      })
      .catch(console.error);
  }, [session]);

  const selectedGuild = guilds.find(g => g.id === currentGuildId);
  const isAdmin = selectedGuild ? (BigInt(selectedGuild.permissions) & BigInt(0x8)) !== BigInt(0) : false;

  const selectGuild = (id: string) => {
    router.push(`${pathname}?guild=${id}`);
  };

  return (
    <aside className="glass-card" style={{
      width: "260px",
      height: "calc(100vh - 4rem)",
      position: "fixed",
      left: "2rem",
      top: "2rem",
      display: "flex",
      flexDirection: "column",
      padding: "2rem 1.5rem"
    }}>
      <div style={{ marginBottom: "3rem" }}>
        <h2 className="accent-text" style={{ fontSize: "1.5rem" }}>UtilityBot</h2>
      </div>

      {/* Server selector */}
      <div style={{ marginBottom: "2rem" }}>
        <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>Select Server</p>
        <select
          value={currentGuildId}
          onChange={e => selectGuild(e.target.value)}
          style={{ width: "100%", padding: "0.8rem", background: "rgba(255,255,255,0.05)", border: "1px solid var(--card-border)", borderRadius: "8px", color: "white" }}
        >
          <option value="">Choose a server…</option>
          {guilds.map(g => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem", flex: 1 }}>
        <Link href={`/dashboard?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard' ? 'active' : ''}`}>Overview</Link>
        <Link href={`/dashboard/stats?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard/stats' ? 'active' : ''}`}>Leaderboards</Link>
        <Link href={`/dashboard/tamagotchi?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard/tamagotchi' ? 'active' : ''}`}>Tamagotchi</Link>
        {isAdmin ? (
          <Link href={`/dashboard/settings?guild=${currentGuildId}`} className={`nav-item ${pathname === '/dashboard/settings' ? 'active' : ''}`}>Server Settings</Link>
        ) : (
          <div className="nav-item locked" style={{ opacity: 0.5, cursor: "not-allowed" }}>Server Settings 🔒</div>
        )}
      </nav>

      {/* User Info */}
      <div style={{ borderTop: "1px solid var(--card-border)", paddingTop: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {session?.user?.image && (
            <img src={session.user.image} alt="Avatar" style={{ width: "40px", height: "40px", borderRadius: "50%" }} />
          )}
          <div>
            <p style={{ fontSize: "0.9rem", fontWeight: 600 }}>{session?.user?.name}</p>
            <button onClick={() => signOut({ callbackUrl: '/' })} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "0.7rem", cursor: "pointer" }}>Sign Out</button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .nav-item {
          padding: 0.8rem 1.2rem;
          border-radius: 12px;
          transition: all 0.2s;
          color: var(--text-muted);
          font-weight: 500;
          text-decoration: none;
        }
        .nav-item:hover:not(.locked) {
          background: rgba(255,255,255,0.05);
          color: white;
        }
        .nav-item.active {
          background: rgba(139,92,246,0.1);
          color: var(--accent);
          border-left: 3px solid var(--accent);
        }
      `}</style>
    </aside>
  );
};

const Sidebar = () => (
  <Suspense fallback={<aside className="glass-card" style={{ width: "260px", height: "calc(100vh - 4rem)", position: "fixed", left: "2rem", top: "2rem" }}></aside>}>
    <SidebarContent />
  </Suspense>
);

export default Sidebar;

