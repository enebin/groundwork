// Taskfold: a small task tool for teams. Fixture for the groundwork journey benchmark.
// Usage: PORT=4310 DATA_DIR=./data [PUBLIC_URL=http://localhost:4310] node server.js
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 4310);
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');
const DB_FILE = path.join(DATA_DIR, 'db.json');
const BASE = process.env.PUBLIC_URL || `http://localhost:${PORT}`;

const emptyDb = () => ({ users: [], sessions: {}, verifyTokens: {}, orgs: [], invites: [], projects: [], emails: [] });

function load() {
  try { return JSON.parse(fs.readFileSync(DB_FILE, 'utf8')); } catch { return emptyDb(); }
}
function save(db) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const token = () => crypto.randomBytes(12).toString('hex');

function sendMail(db, to, subject, body) {
  db.emails.push({ to, subject, body, at: new Date().toISOString() });
}

const css = `
body{font-family:system-ui,sans-serif;margin:0;color:#1d2330;background:#f7f8fa}
header{display:flex;justify-content:space-between;align-items:center;padding:14px 28px;background:#fff;border-bottom:1px solid #e3e6eb}
header a{color:#1d2330;text-decoration:none;margin-left:18px}
.brand{font-weight:700;font-size:18px}
main{max-width:760px;margin:36px auto;padding:0 20px}
.hero{text-align:center;padding:60px 20px}
.hero h1{font-size:40px;margin:0 0 12px}
.hero p{font-size:18px;color:#4a5263}
.btn{display:inline-block;background:#3b5bdb;color:#fff;border:0;border-radius:6px;padding:11px 20px;font-size:15px;text-decoration:none;cursor:pointer}
.btn[disabled]{background:#aab4c8;cursor:not-allowed}
.btn.secondary{background:#fff;color:#3b5bdb;border:1px solid #3b5bdb}
.card{background:#fff;border:1px solid #e3e6eb;border-radius:8px;padding:24px;margin-bottom:20px}
label{display:block;margin:14px 0 6px;font-weight:600}
input,textarea{width:100%;box-sizing:border-box;padding:9px;border:1px solid #c9ced8;border-radius:6px;font-size:15px}
.error{background:#fdecec;color:#a61b1b;padding:10px;border-radius:6px}
.notice{background:#e8f4ea;color:#1d6b2c;padding:10px;border-radius:6px}
.features{display:flex;gap:16px;margin:30px 0}
.features div{flex:1;background:#fff;border:1px solid #e3e6eb;border-radius:8px;padding:16px}
footer{text-align:center;color:#8a91a0;font-size:12px;padding:40px 0}
footer a{color:#8a91a0}
details.menu{position:relative;display:inline-block}
details.menu summary{list-style:none;cursor:pointer;padding:4px 10px;border:1px solid #c9ced8;border-radius:6px}
details.menu .items{position:absolute;right:0;background:#fff;border:1px solid #e3e6eb;border-radius:6px;padding:6px 0;min-width:160px}
details.menu .items a{display:block;padding:6px 14px;color:#1d2330;text-decoration:none}
.muted{color:#8a91a0}
`;

function page(title, body, user) {
  const nav = user
    ? `<a href="/app">Dashboard</a><a href="/app/members">Members</a><a href="/signout">Sign out</a>`
    : `<a href="/#features">Features</a><a href="/pricing">Pricing</a><a href="/signin">Sign in</a>`;
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} · Taskfold</title><style>${css}</style></head>
<body><header><a class="brand" href="${user ? '/app' : '/'}">Taskfold</a><nav>${nav}</nav></header><main>${body}</main></body></html>`;
}

function parseCookies(req) {
  return Object.fromEntries((req.headers.cookie || '').split(';').filter(Boolean).map((c) => c.trim().split('=').map(decodeURIComponent)));
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (c) => (data += c));
    req.on('end', () => resolve(Object.fromEntries(new URLSearchParams(data))));
  });
}

function redirect(res, to, headers = {}) {
  res.writeHead(303, { Location: to, ...headers });
  res.end();
}

function html(res, body, status = 200) {
  res.writeHead(status, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(body);
}

function currentUser(db, req) {
  const sid = parseCookies(req).sid;
  const email = sid && db.sessions[sid];
  return email ? db.users.find((u) => u.email === email) : null;
}

function signIn(db, res, email, to) {
  const sid = token();
  db.sessions[sid] = email;
  save(db);
  redirect(res, to, { 'Set-Cookie': `sid=${sid}; Path=/; HttpOnly` });
}

const landing = () => `
<section class="hero">
  <h1>Your team's tasks, folded into one place</h1>
  <p>Taskfold keeps small teams on the same page: shared projects, clear owners, and no status meetings.</p>
  <p><a class="btn" href="/demo">Book a demo</a></p>
</section>
<section id="features" class="features">
  <div><strong>Shared projects</strong><p class="muted">Everyone sees the same list, in real time.</p></div>
  <div><strong>Clear owners</strong><p class="muted">Every task has one person responsible.</p></div>
  <div><strong>Made for 2–20</strong><p class="muted">Built for studios, agencies, and small startups.</p></div>
</section>
<footer>© Taskfold · <a href="/pricing">Pricing</a> · <a href="/signup">Create a free account</a> · <a href="/privacy">Privacy</a></footer>`;

const signupForm = (error) => `
<div class="card"><h2>Create your Taskfold account</h2>
${error ? `<p class="error">${esc(error)}</p>` : ''}
<form method="post" action="/signup">
  <label for="name">Full name</label><input id="name" name="name">
  <label for="email">Work email</label><input id="email" name="email" type="email">
  <label for="password">Password</label><input id="password" name="password" type="password">
  <p><button class="btn" type="submit">Create account</button></p>
</form></div>`;

const signinForm = (error) => `
<div class="card"><h2>Sign in to Taskfold</h2>
${error ? `<p class="error">${esc(error)}</p>` : ''}
<form method="post" action="/signin">
  <label for="email">Email</label><input id="email" name="email" type="email">
  <label for="password">Password</label><input id="password" name="password" type="password">
  <p><button class="btn" type="submit">Sign in</button></p>
</form></div>`;

const orgForm = () => `
<div class="card"><h2>Set up your organization</h2>
<p class="muted">Your organization is where your team's projects live.</p>
<form method="post" action="/onboarding/org">
  <label for="org-name">Organization name</label><input id="org-name" name="name">
  <label for="slug">Workspace URL</label><input id="slug" name="slug" placeholder="taskfold.app/">
  <p><button class="btn" id="continue" type="submit" disabled>Continue</button></p>
</form></div>
<script>
const slug = document.getElementById('slug'), name = document.getElementById('org-name'), btn = document.getElementById('continue');
function check() { btn.disabled = !(name.value.trim() && /^[a-z0-9-]{3,}$/.test(slug.value)); }
slug.addEventListener('input', check); name.addEventListener('input', check);
</script>`;

function dashboard(db, user) {
  const org = db.orgs.find((o) => o.id === user.orgId);
  const projects = db.projects.filter((p) => p.orgId === org.id);
  const list = projects.length
    ? `<ul>${projects.map((p) => `<li>${esc(p.name)}</li>`).join('')}</ul>`
    : `<p class="muted">No projects yet.</p>`;
  return `
<div style="display:flex;justify-content:space-between;align-items:center">
  <h2>${esc(org.name)}</h2>
  <details class="menu"><summary aria-label="More">⋯</summary><div class="items"><a href="/app/projects/new">New project</a><a href="/app/settings">Settings</a></div></details>
</div>
<div class="card"><h3>Projects</h3>${list}</div>
<div class="card"><h3>Your tasks</h3><p class="muted">Nothing assigned to you.</p></div>`;
}

function members(db, user) {
  const org = db.orgs.find((o) => o.id === user.orgId);
  const people = db.users.filter((u) => u.orgId === org.id);
  return `<div class="card"><h2>Members of ${esc(org.name)}</h2>
<ul>${people.map((u) => `<li>${esc(u.name)} — ${esc(u.email)}${u.email === org.owner ? ' (owner)' : ''}</li>`).join('')}</ul>
<p><a class="btn" href="/app/invite">Invite people</a></p></div>`;
}

const inviteForm = () => `<div class="card"><h2>Invite people</h2>
<form method="post" action="/app/invite">
  <label for="invite-email">Email address</label><input id="invite-email" name="email" type="email">
  <p><button class="btn" type="submit">Send invite</button></p>
</form></div>`;

const projectForm = () => `<div class="card"><h2>New project</h2>
<form method="post" action="/app/projects/new">
  <label for="project-name">Project name</label><input id="project-name" name="name">
  <p><button class="btn" type="submit">Create project</button></p>
</form></div>`;

function inbox(db, to) {
  const mails = db.emails.filter((m) => !to || m.to === to).reverse();
  const items = mails.length
    ? mails.map((m) => `<div class="card"><p class="muted">To: ${esc(m.to)} · ${esc(m.at)}</p><h3>${esc(m.subject)}</h3><p>${m.body}</p></div>`).join('')
    : `<p class="muted">No messages.</p>`;
  return `<h2>Dev inbox${to ? ` — ${esc(to)}` : ''}</h2>${items}`;
}

async function handle(req, res) {
  const url = new URL(req.url, BASE);
  const p = url.pathname;
  const db = load();
  const user = currentUser(db, req);
  const post = req.method === 'POST';

  if (p === '/' && !post) return html(res, page('Home', landing(), null));
  if (p === '/pricing') return html(res, page('Pricing', `<div class="card"><h2>Pricing</h2><p>Free for teams up to 5. Team plan: $6 per person per month.</p><p><a class="btn" href="/demo">Talk to sales</a></p></div>`, user));
  if (p === '/privacy') return html(res, page('Privacy', `<div class="card"><h2>Privacy</h2><p>We store only what we need to run Taskfold.</p></div>`, user));
  if (p === '/demo' && !post) return html(res, page('Book a demo', `<div class="card"><h2>Book a demo</h2><form method="post" action="/demo"><label for="d-name">Name</label><input id="d-name" name="name"><label for="d-email">Work email</label><input id="d-email" name="email"><label for="d-size">Team size</label><input id="d-size" name="size"><p><button class="btn" type="submit">Request demo</button></p></form></div>`, user));
  if (p === '/demo' && post) return html(res, page('Thanks', `<div class="card"><h2>Thanks!</h2><p>Our sales team will reach out within 2 business days.</p></div>`, user));

  if (p === '/signup' && !post) return html(res, page('Sign up', signupForm(), null));
  if (p === '/signup' && post) {
    const f = await readBody(req);
    const email = (f.email || '').trim().toLowerCase();
    const strong = (f.password || '').length >= 10 && /\d/.test(f.password || '');
    if (!f.name || !email || !strong || db.users.some((u) => u.email === email)) {
      return html(res, page('Sign up', signupForm('Something went wrong. Please try again.'), null), 400);
    }
    db.users.push({ name: f.name.trim(), email, password: f.password, verified: false, orgId: null });
    const t = token();
    db.verifyTokens[t] = email;
    sendMail(db, email, 'Confirm your Taskfold email', `Hi ${esc(f.name)}, confirm your email to start using Taskfold: <a href="${BASE}/verify?token=${t}">Confirm email</a>`);
    save(db);
    return html(res, page('Check your email', `<div class="card"><h2>Check your email</h2><p>We sent a confirmation link to <strong>${esc(email)}</strong>.</p></div>`, null));
  }
  if (p === '/verify') {
    const email = db.verifyTokens[url.searchParams.get('token')];
    const u = email && db.users.find((x) => x.email === email);
    if (!u) return html(res, page('Link expired', `<div class="card"><h2>This link has expired</h2></div>`, null), 400);
    u.verified = true;
    delete db.verifyTokens[url.searchParams.get('token')];
    save(db);
    return redirect(res, '/signin');
  }

  if (p === '/signin' && !post) return html(res, page('Sign in', signinForm(), null));
  if (p === '/signin' && post) {
    const f = await readBody(req);
    const u = db.users.find((x) => x.email === (f.email || '').trim().toLowerCase() && x.password === f.password);
    if (!u) return html(res, page('Sign in', signinForm('Email or password is incorrect.'), null), 400);
    if (!u.verified) return html(res, page('Sign in', signinForm('Please confirm your email first. Check your inbox for the link.'), null), 400);
    return signIn(db, res, u.email, u.orgId ? '/app' : '/onboarding/org');
  }
  if (p === '/signout') return redirect(res, '/', { 'Set-Cookie': 'sid=; Path=/; Max-Age=0' });

  if (p === '/invite/accept') {
    const inv = db.invites.find((i) => i.token === (url.searchParams.get('token') || '') && !i.accepted);
    if (!inv) return html(res, page('Invitation', `<div class="card"><h2>This invitation is no longer valid</h2><p>Ask the person who invited you to send a new one.</p></div>`, null), 400);
    const org = db.orgs.find((o) => o.id === inv.orgId);
    if (!post) {
      return html(res, page('Join', `<div class="card"><h2>Join ${esc(org.name)} on Taskfold</h2><p class="muted">You were invited as ${esc(inv.email)}.</p>
<form method="post"><label for="j-name">Your name</label><input id="j-name" name="name"><label for="j-password">Choose a password</label><input id="j-password" name="password" type="password"><p class="muted">At least 10 characters, including a number.</p><p><button class="btn" type="submit">Join ${esc(org.name)}</button></p></form></div>`, null));
    }
    const f = await readBody(req);
    if (!f.name || (f.password || '').length < 10 || !/\d/.test(f.password)) {
      return html(res, page('Join', `<div class="card"><p class="error">Enter your name and a password of at least 10 characters with a number.</p><p><a href="${esc(req.url)}">Try again</a></p></div>`, null), 400);
    }
    db.users.push({ name: f.name.trim(), email: inv.email, password: f.password, verified: true, orgId: org.id });
    inv.accepted = true;
    return signIn(db, res, inv.email, '/app');
  }

  if (p.startsWith('/dev/')) {
    if (p === '/dev/inbox') return html(res, page('Dev inbox', inbox(db, url.searchParams.get('to')), null));
    if (p === '/dev/login') return signIn(db, res, url.searchParams.get('email'), '/app');
  }

  if (p.startsWith('/app') || p.startsWith('/onboarding')) {
    if (!user) return redirect(res, '/signin');
    if (p === '/onboarding/org' && !post) return html(res, page('Set up', orgForm(), user));
    if (p === '/onboarding/org' && post) {
      const f = await readBody(req);
      const id = token();
      db.orgs.push({ id, name: f.name.trim(), slug: f.slug, owner: user.email });
      user.orgId = id;
      save(db);
      return redirect(res, '/app');
    }
    if (!user.orgId) return redirect(res, '/onboarding/org');
    if (p === '/app') return html(res, page('Dashboard', dashboard(db, user), user));
    if (p === '/app/members') return html(res, page('Members', members(db, user), user));
    if (p === '/app/settings') return html(res, page('Settings', `<div class="card"><h2>Settings</h2><p class="muted">Billing and integrations are coming soon.</p></div>`, user));
    if (p === '/app/invite' && !post) return html(res, page('Invite', inviteForm(), user));
    if (p === '/app/invite' && post) {
      const f = await readBody(req);
      const email = (f.email || '').trim().toLowerCase();
      if (email) {
        const t = token();
        const org = db.orgs.find((o) => o.id === user.orgId);
        db.invites.push({ token: t, email, orgId: org.id, invitedBy: user.email, accepted: false });
        sendMail(db, email, `${user.name} invited you to ${org.name} on Taskfold`, `<a href="${BASE}/invite/accept?token=${t}">Accept the invitation</a>`);
        save(db);
      }
      return redirect(res, '/app/invite');
    }
    if (p === '/app/projects/new' && !post) return html(res, page('New project', projectForm(), user));
    if (p === '/app/projects/new' && post) {
      const f = await readBody(req);
      if (f.name && f.name.trim()) db.projects.push({ orgId: user.orgId, name: f.name.trim(), createdBy: user.email });
      save(db);
      return redirect(res, '/app');
    }
  }

  html(res, page('Not found', `<div class="card"><h2>Page not found</h2><p><a href="/">Go home</a></p></div>`, user), 404);
}

http.createServer((req, res) => handle(req, res).catch((e) => {
  console.error(e);
  html(res, 'Server error', 500);
})).listen(PORT, () => console.log(`Taskfold on ${BASE} (data: ${DB_FILE})`));
