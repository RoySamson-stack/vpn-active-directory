import React, { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [token, setToken] = useState(localStorage.getItem('vpn_token'))
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [sessions, setSessions] = useState([])
  const [stats, setStats] = useState(null)

  const api = axios.create({
    baseURL: API_URL,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const response = await api.post('/api/v1/auth/login', { username, password })
      const newToken = response.data.access_token
      setToken(newToken)
      localStorage.setItem('vpn_token', newToken)
      api.defaults.headers.Authorization = `Bearer ${newToken}`
    } catch (error) {
      alert('Login failed: ' + (error.response?.data?.detail || error.message))
    }
  }

  const loadSessions = async () => {
    try {
      const response = await api.get('/api/v1/sessions/')
      setSessions(response.data)
    } catch (error) {
      alert('Failed to load sessions: ' + (error.response?.data?.detail || error.message))
    }
  }

  const loadStats = async () => {
    try {
      const response = await api.get('/api/v1/analytics/dashboard')
      setStats(response.data)
    } catch (error) {
      alert('Failed to load stats: ' + (error.response?.data?.detail || error.message))
    }
  }

  const createSession = async () => {
    try {
      // Generate keys (simplified - in production use proper key generation)
      const response = await api.post('/api/v1/sessions/', {
        client_public_key: 'placeholder_key',
        client_ip: '0.0.0.0',
        protocol: 'wireguard',
        hop_count: 1
      })
      alert('Session created: ' + response.data.session_id)
      loadSessions()
    } catch (error) {
      alert('Failed to create session: ' + (error.response?.data?.detail || error.message))
    }
  }

  if (!token) {
    return (
      <div className="container">
        <h1>Enterprise VPN Dashboard</h1>
        <form onSubmit={handleLogin} className="login-form">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Login</button>
        </form>
      </div>
    )
  }

  return (
    <div className="container">
      <header>
        <h1>Enterprise VPN Dashboard</h1>
        <button onClick={() => {
          setToken(null)
          localStorage.removeItem('vpn_token')
        }}>Logout</button>
      </header>

      <div className="dashboard">
        <section className="stats">
          <h2>Statistics</h2>
          <button onClick={loadStats}>Refresh Stats</button>
          {stats && (
            <div className="stat-grid">
              <div className="stat-card">
                <h3>Active Sessions</h3>
                <p>{stats.active_sessions}</p>
              </div>
              <div className="stat-card">
                <h3>Total (24h)</h3>
                <p>{stats.total_sessions_24h}</p>
              </div>
              <div className="stat-card">
                <h3>Bandwidth</h3>
                <p>{(stats.total_bandwidth_bytes / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <div className="stat-card">
                <h3>Engagements</h3>
                <p>{stats.active_engagements}</p>
              </div>
            </div>
          )}
        </section>

        <section className="sessions">
          <h2>VPN Sessions</h2>
          <div className="actions">
            <button onClick={loadSessions}>Refresh</button>
            <button onClick={createSession}>Create Session</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Status</th>
                <th>Protocol</th>
                <th>Hops</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(session => (
                <tr key={session.id}>
                  <td>{session.session_id.substring(0, 16)}...</td>
                  <td>{session.status}</td>
                  <td>{session.protocol}</td>
                  <td>{session.hop_count}</td>
                  <td>{new Date(session.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  )
}

export default App

