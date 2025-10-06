"use client";
import { useState } from "react";

export default function Home() {
  const [role, setRole] = useState("Frontend Engineer");
  const [difficulty, setDifficulty] = useState("Intermediate");
  const [domain, setDomain] = useState("CoverageX");
  const [jd, setJd] = useState("Need to have knowledge in HTML,CSS and Javascript");
  const [loading, setLoading] = useState(false);

  async function createSession() {
    setLoading(true);
    const res = await fetch("http://localhost:8000/sessions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, difficulty, domain, job_description: jd }),
    });
    const data = await res.json();
    window.location.href = `/interview/${data.session_id}`;
  }

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-3xl font-bold">Start AI Interview</h1>
      <div className="grid gap-3">
        <input className="border p-2 rounded" placeholder="Role (e.g., Backend Engineer)" value={role} onChange={e=>setRole(e.target.value)} />
        <select className="border p-2 rounded" value={difficulty} onChange={e=>setDifficulty(e.target.value)}>
          { ["Junior","Intermediate","Senior"].map(x=> <option key={x}>{x}</option>) }
        </select>
        <input className="border p-2 rounded" placeholder="Domain (e.g., FinTech)" value={domain} onChange={e=>setDomain(e.target.value)} />
        <textarea className="border p-2 rounded" rows={5} placeholder="Job Description / Focus Areas" value={jd} onChange={e=>setJd(e.target.value)} />
        <button className="bg-black text-white rounded p-3 disabled:opacity-50" onClick={createSession} disabled={!role || loading}>{loading?"Preparing...":"Create Session"}</button>
      </div>
    </main>
  );
}