async function check() {
  const el = document.getElementById('status')
  try {
    const r = await fetch('http://127.0.0.1:8000/health')
    const d = await r.json()
    el.textContent = d.status || 'ok'
  } catch {
    el.textContent = 'down'
  }
}
document.getElementById('checkBtn').addEventListener('click', check)
check()
