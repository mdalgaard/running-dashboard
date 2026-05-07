// api/checkin.js — Vercel serverless function
// Receives check-in POSTs from the dashboard and writes to checkins.json via GitHub API

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).end();

  const { feel, note } = req.body;
  if (!feel) return res.status(400).json({ error: 'Missing feel' });

  const token  = process.env.GITHUB_TOKEN;
  const owner  = process.env.GITHUB_OWNER;   // e.g. "mdalgaard"
  const repo   = process.env.GITHUB_REPO;    // e.g. "running-dashboard"
  const path   = 'public/checkins.json';

  // 1. Get current file
  const getRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' }
  });
  const fileData = await getRes.json();
  const current  = JSON.parse(Buffer.from(fileData.content, 'base64').toString());

  // 2. Append new entry
  const entry = {
    date: new Date().toISOString().split('T')[0],
    time: new Date().toUTCString().slice(17, 22),
    feel, note: note || ''
  };
  current.unshift(entry);
  if (current.length > 60) current.pop();

  // 3. Write back
  const content = Buffer.from(JSON.stringify(current, null, 2)).toString('base64');
  await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: `checkin: ${feel} — ${entry.date}`, content, sha: fileData.sha })
  });

  res.status(200).json({ ok: true });
}
