// api/checkin.js — replace the whole file with this
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).end();

  const { feel, note } = req.body;
  if (!feel) return res.status(400).json({ error: 'Missing feel' });

  const token = process.env.GITHUB_TOKEN;
  const owner = process.env.GITHUB_OWNER;
  const repo  = process.env.GITHUB_REPO;
  const path  = 'public/checkins.json';

  const getRes  = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' }
  });
  const fileData = await getRes.json();
  const current  = JSON.parse(Buffer.from(fileData.content, 'base64').toString());

  const entry = {
    date: new Date().toISOString().split('T')[0],
    time: new Date().toUTCString().slice(17, 22),
    feel,
    note: note || ''
  };
  current.unshift(entry);
  if (current.length > 60) current.pop();

  const content = Buffer.from(JSON.stringify(current, null, 2)).toString('base64');
  await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: `checkin: ${feel} — ${entry.date}`,
      content,
      sha: fileData.sha
    })
  });

  return res.status(200).json({ ok: true });
};
