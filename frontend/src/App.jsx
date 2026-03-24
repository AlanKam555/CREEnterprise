import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

// ============ API CLIENT ============
const API = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

API.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ============ ICONS ============
const Icons = {
  Building: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="8" y2="10"/><line x1="16" y1="6" x2="16" y2="10"/><line x1="8" y1="14" x2="8" y2="18"/><line x1="16" y1="14" x2="16" y2="18"/></svg>,
  TrendingUp: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 17"/><polyline points="17 6 23 6 23 12"/></svg>,
  DollarSign: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>,
  BarChart: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>,
  Plus: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  X: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
  Check: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>,
  Loader: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="animate-spin"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>,
  LogOut: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
  Menu: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
  Home: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>,
  Edit: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  Trash: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>,
  Download: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
}

// ============ SIDEBAR ============
function Sidebar({ active, setActive, onLogout }) {
  const nav = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.Home },
    { id: 'properties', label: 'Properties', icon: Icons.Building },
    { id: 'valuations', label: 'Valuations', icon: Icons.DollarSign },
    { id: 'rentroll', label: 'Rent Roll', icon: Icons.BarChart },
    { id: 'memos', label: 'Memos', icon: Icons.Edit },
  ]

  return (
    <nav className="w-56 bg-cre-surface border-r border-cre-border flex flex-col py-4 shrink-0">
      <div className="px-4 mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-cre-blue/20 flex items-center justify-center text-cre-blue text-xl">
          <Icons.Building />
        </div>
        <div>
          <p className="text-white font-bold text-sm">CRE Suite</p>
          <p className="text-gray-500 text-xs">Enterprise Edition</p>
        </div>
      </div>

      <div className="flex-1 px-3 space-y-1">
        {nav.map(item => (
          <button key={item.id} onClick={() => setActive(item.id)}
            className={`w-full nav-item ${active === item.id ? 'active' : ''}`}>
            <item.icon />
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      <div className="px-4 pt-4 border-t border-cre-border">
        <button onClick={onLogout} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-cre-surface/50 transition-all text-sm">
          <Icons.LogOut />
          <span>Logout</span>
        </button>
      </div>
    </nav>
  )
}

// ============ DASHBOARD PAGE ============
function Dashboard({ user }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      try {
        const res = await API.get('/dashboard')
        setStats(res.data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Welcome back, {user?.username || 'User'}</p>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400"><Icons.Loader /> Loading...</div>
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="cre-card">
            <p className="text-gray-400 text-xs mb-1">Total Properties</p>
            <p className="text-3xl font-bold text-cre-blue">{stats.total_properties}</p>
          </div>
          <div className="cre-card">
            <p className="text-gray-400 text-xs mb-1">Total Valuations</p>
            <p className="text-3xl font-bold text-cre-green">{stats.total_valuations}</p>
          </div>
          <div className="cre-card">
            <p className="text-gray-400 text-xs mb-1">Avg IRR</p>
            <p className="text-3xl font-bold text-cre-amber">{stats.avg_irr}%</p>
          </div>
          <div className="cre-card">
            <p className="text-gray-400 text-xs mb-1">Avg DSCR</p>
            <p className="text-3xl font-bold text-cre-blue">{stats.avg_dscr}</p>
          </div>
        </div>
      ) : null}

      <div className="cre-card">
        <h3 className="text-white font-semibold mb-4">Quick Start</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-cre-dark rounded-lg p-4 border border-cre-border hover:border-cre-blue transition-colors cursor-pointer">
            <Icons.Building className="text-cre-blue mb-2" />
            <p className="text-white font-medium text-sm">Add Property</p>
            <p className="text-gray-500 text-xs mt-1">Create a new property</p>
          </div>
          <div className="bg-cre-dark rounded-lg p-4 border border-cre-border hover:border-cre-blue transition-colors cursor-pointer">
            <Icons.DollarSign className="text-cre-green mb-2" />
            <p className="text-white font-medium text-sm">Valuation</p>
            <p className="text-gray-500 text-xs mt-1">Calculate IRR & metrics</p>
          </div>
          <div className="bg-cre-dark rounded-lg p-4 border border-cre-border hover:border-cre-blue transition-colors cursor-pointer">
            <Icons.Edit className="text-cre-amber mb-2" />
            <p className="text-white font-medium text-sm">Memo</p>
            <p className="text-gray-500 text-xs mt-1">Generate investor memo</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============ PROPERTIES PAGE ============
function Properties() {
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', asset_type: 'multifamily', address: '', purchase_price: '', purchase_date: '' })

  const loadProperties = useCallback(async () => {
    try {
      const res = await API.get('/properties')
      setProperties(res.data.properties || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadProperties() }, [loadProperties])

  const handleCreate = async () => {
    if (!form.name || !form.address) return
    try {
      await API.post('/properties', form)
      setForm({ name: '', asset_type: 'multifamily', address: '', purchase_price: '', purchase_date: '' })
      setShowCreate(false)
      loadProperties()
    } catch (e) { console.error(e) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Properties</h1>
          <p className="text-gray-400 text-sm mt-1">Manage your real estate portfolio</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="cre-btn-primary flex items-center gap-2">
          <Icons.Plus /> Add Property
        </button>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-cre-surface border border-cre-border rounded-2xl p-6 w-full max-w-lg">
            <h3 className="text-white font-bold text-lg mb-4">Add Property</h3>
            <div className="space-y-4">
              <input placeholder="Property Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
              <select value={form.asset_type} onChange={e => setForm({...form, asset_type: e.target.value})}>
                <option value="multifamily">Multifamily</option>
                <option value="industrial">Industrial</option>
                <option value="mixed-use">Mixed-Use</option>
                <option value="commercial">Commercial</option>
                <option value="land">Land & Development</option>
              </select>
              <input placeholder="Address" value={form.address} onChange={e => setForm({...form, address: e.target.value})} />
              <input type="number" placeholder="Purchase Price" value={form.purchase_price} onChange={e => setForm({...form, purchase_price: e.target.value})} />
              <input type="date" value={form.purchase_date} onChange={e => setForm({...form, purchase_date: e.target.value})} />
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowCreate(false)} className="cre-btn-ghost flex-1">Cancel</button>
              <button onClick={handleCreate} className="cre-btn-primary flex-1">Create</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-gray-400"><Icons.Loader /> Loading...</div>
      ) : properties.length === 0 ? (
        <div className="cre-card text-center py-16">
          <Icons.Building className="text-4xl mx-auto mb-4 text-gray-500" />
          <h3 className="text-white font-semibold text-lg mb-2">No Properties</h3>
          <p className="text-gray-400 text-sm">Create your first property to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {properties.map(prop => (
            <div key={prop.id} className="cre-card">
              <h3 className="text-white font-semibold">{prop.name}</h3>
              <p className="text-gray-400 text-xs mt-1">{prop.asset_type}</p>
              <p className="text-gray-500 text-xs mt-2">{prop.address}</p>
              <p className="text-cre-blue font-semibold mt-3">${parseFloat(prop.purchase_price).toLocaleString()}</p>
              <div className="flex gap-2 mt-4">
                <button className="cre-btn-ghost text-xs flex-1">View</button>
                <button className="cre-btn-ghost text-xs flex-1">Edit</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============ VALUATIONS PAGE ============
function Valuations() {
  const [properties, setProperties] = useState([])
  const [selectedProp, setSelectedProp] = useState(null)
  const [form, setForm] = useState({ noi: '', cap_rate: '', debt_service: '', equity_invested: '' })
  const [result, setResult] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await API.get('/properties')
        setProperties(res.data.properties || [])
      } catch (e) { console.error(e) }
    }
    load()
  }, [])

  const handleCalculate = async () => {
    if (!selectedProp || !form.noi) return
    try {
      const res = await API.post('/valuations', {
        property_id: selectedProp,
        valuation_type: 'standard',
        noi: parseFloat(form.noi),
        cap_rate: parseFloat(form.cap_rate) || 5,
        debt_service: parseFloat(form.debt_service) || 0,
        equity_invested: parseFloat(form.equity_invested) || 0
      })
      setResult(res.data.valuation)
    } catch (e) { console.error(e) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Valuations</h1>
        <p className="text-gray-400 text-sm mt-1">Calculate IRR, CoC, DSCR & more</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="cre-card">
          <h3 className="text-white font-semibold mb-4">Valuation Calculator</h3>
          <div className="space-y-4">
            <div>
              <label className="text-gray-400 text-xs mb-1 block">Property</label>
              <select value={selectedProp || ''} onChange={e => setSelectedProp(e.target.value)}>
                <option value="">Select Property</option>
                {properties.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-gray-400 text-xs mb-1 block">NOI ($)</label>
              <input type="number" placeholder="Net Operating Income" value={form.noi} onChange={e => setForm({...form, noi: e.target.value})} />
            </div>
            <div>
              <label className="text-gray-400 text-xs mb-1 block">Cap Rate (%)</label>
              <input type="number" placeholder="Capitalization Rate" value={form.cap_rate} onChange={e => setForm({...form, cap_rate: e.target.value})} />
            </div>
            <div>
              <label className="text-gray-400 text-xs mb-1 block">Debt Service ($)</label>
              <input type="number" placeholder="Annual Debt Service" value={form.debt_service} onChange={e => setForm({...form, debt_service: e.target.value})} />
            </div>
            <div>
              <label className="text-gray-400 text-xs mb-1 block">Equity Invested ($)</label>
              <input type="number" placeholder="Equity Investment" value={form.equity_invested} onChange={e => setForm({...form, equity_invested: e.target.value})} />
            </div>
            <button onClick={handleCalculate} className="cre-btn-primary w-full">Calculate</button>
          </div>
        </div>

        {result && (
          <div className="cre-card">
            <h3 className="text-white font-semibold mb-4">Results</h3>
            <div className="space-y-3">
              <div className="bg-cre-dark rounded-lg p-3">
                <p className="text-gray-400 text-xs">IRR</p>
                <p className="text-2xl font-bold text-cre-green">{result.irr}%</p>
              </div>
              <div className="bg-cre-dark rounded-lg p-3">
                <p className="text-gray-400 text-xs">Cash-on-Cash</p>
                <p className="text-2xl font-bold text-cre-blue">{result.coc}%</p>
              </div>
              <div className="bg-cre-dark rounded-lg p-3">
                <p className="text-gray-400 text-xs">DSCR</p>
                <p className="text-2xl font-bold text-cre-amber">{result.dscr}</p>
              </div>
              <div className="bg-cre-dark rounded-lg p-3">
                <p className="text-gray-400 text-xs">Cap Rate</p>
                <p className="text-2xl font-bold text-cre-blue">{result.cap_rate}%</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ============ RENT ROLL PAGE ============
function RentRoll() {
  const [properties, setProperties] = useState([])
  const [selectedProp, setSelectedProp] = useState(null)
  const [rentRoll, setRentRoll] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ unit_number: '', tenant_name: '', lease_start: '', lease_end: '', monthly_rent: '', status: 'occupied' })

  useEffect(() => {
    const load = async () => {
      try {
        const res = await API.get('/properties')
        setProperties(res.data.properties || [])
      } catch (e) { console.error(e) }
    }
    load()
  }, [])

  useEffect(() => {
    if (!selectedProp) return
    const load = async () => {
      try {
        const res = await API.get(`/properties/${selectedProp}/rent-roll`)
        setRentRoll(res.data)
      } catch (e) { console.error(e) }
    }
    load()
  }, [selectedProp])

  const handleAdd = async () => {
    if (!selectedProp || !form.unit_number) return
    try {
      await API.post(`/properties/${selectedProp}/rent-roll`, form)
      setForm({ unit_number: '', tenant_name: '', lease_start: '', lease_end: '', monthly_rent: '', status: 'occupied' })
      setShowAdd(false)
      // Reload rent roll
      const res = await API.get(`/properties/${selectedProp}/rent-roll`)
      setRentRoll(res.data)
    } catch (e) { console.error(e) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Rent Roll</h1>
          <p className="text-gray-400 text-sm mt-1">Manage tenant information</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="cre-btn-primary flex items-center gap-2">
          <Icons.Plus /> Add Unit
        </button>
      </div>

      <div className="cre-card">
        <label className="text-gray-400 text-xs mb-2 block">Select Property</label>
        <select value={selectedProp || ''} onChange={e => setSelectedProp(e.target.value)}>
          <option value="">Choose a property...</option>
          {properties.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-cre-surface border border-cre-border rounded-2xl p-6 w-full max-w-lg">
            <h3 className="text-white font-bold text-lg mb-4">Add Unit</h3>
            <div className="space-y-4">
              <input placeholder="Unit Number" value={form.unit_number} onChange={e => setForm({...form, unit_number: e.target.value})} />
              <input placeholder="Tenant Name" value={form.tenant_name} onChange={e => setForm({...form, tenant_name: e.target.value})} />
              <input type="date" placeholder="Lease Start" value={form.lease_start} onChange={e => setForm({...form, lease_start: e.target.value})} />
              <input type="date" placeholder="Lease End" value={form.lease_end} onChange={e => setForm({...form, lease_end: e.target.value})} />
              <input type="number" placeholder="Monthly Rent" value={form.monthly_rent} onChange={e => setForm({...form, monthly_rent: e.target.value})} />
              <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}>
                <option value="occupied">Occupied</option>
                <option value="vacant">Vacant</option>
              </select>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowAdd(false)} className="cre-btn-ghost flex-1">Cancel</button>
              <button onClick={handleAdd} className="cre-btn-primary flex-1">Add</button>
            </div>
          </div>
        </div>
      )}

      {rentRoll && (
        <div className="cre-card">
          <h3 className="text-white font-semibold mb-4">Summary</h3>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-cre-dark rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs">Total Units</p>
              <p className="text-2xl font-bold text-cre-blue">{rentRoll.total_units}</p>
            </div>
            <div className="bg-cre-dark rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs">Occupied</p>
              <p className="text-2xl font-bold text-cre-green">{rentRoll.occupied_units}</p>
            </div>
            <div className="bg-cre-dark rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs">Occupancy</p>
              <p className="text-2xl font-bold text-cre-amber">{rentRoll.occupancy_rate}%</p>
            </div>
            <div className="bg-cre-dark rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs">Monthly Rent</p>
              <p className="text-2xl font-bold text-cre-blue">${(rentRoll.total_monthly_rent / 1000).toFixed(1)}K</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Unit</th>
                  <th>Tenant</th>
                  <th>Lease Start</th>
                  <th>Lease End</th>
                  <th>Monthly Rent</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rentRoll.entries.map((entry, i) => (
                  <tr key={i}>
                    <td className="font-mono text-cre-blue">{entry.unit_number}</td>
                    <td>{entry.tenant_name || '-'}</td>
                    <td className="text-sm">{entry.lease_start}</td>
                    <td className="text-sm">{entry.lease_end}</td>
                    <td className="font-semibold">${entry.monthly_rent.toLocaleString()}</td>
                    <td><span className={`metric-badge ${entry.status === 'occupied' ? 'positive' : 'negative'}`}>{entry.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ============ MEMOS PAGE ============
function Memos() {
  const [properties, setProperties] = useState([])
  const [selectedProp, setSelectedProp] = useState(null)
  const [memo, setMemo] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await API.get('/properties')
        setProperties(res.data.properties || [])
      } catch (e) { console.error(e) }
    }
    load()
  }, [])

  const handleGenerate = async () => {
    if (!selectedProp) return
    setLoading(true)
    try {
      const res = await API.post(`/properties/${selectedProp}/memo`, {
        title: 'Investment Memorandum',
        memo_type: 'investment'
      })
      setMemo(res.data.memo)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Investor Memos</h1>
        <p className="text-gray-400 text-sm mt-1">Generate professional investment memorandums</p>
      </div>

      <div className="cre-card">
        <h3 className="text-white font-semibold mb-4">Generate Memo</h3>
        <div className="space-y-4">
          <div>
            <label className="text-gray-400 text-xs mb-2 block">Select Property</label>
            <select value={selectedProp || ''} onChange={e => setSelectedProp(e.target.value)}>
              <option value="">Choose a property...</option>
              {properties.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <button onClick={handleGenerate} disabled={loading} className="cre-btn-primary w-full flex items-center justify-center gap-2">
            {loading ? <><Icons.Loader /> Generating...</> : <>Generate Memo</>}
          </button>
        </div>
      </div>

      {memo && (
        <div className="cre-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold">Memo</h3>
            <button className="cre-btn-ghost text-xs flex items-center gap-1">
              <Icons.Download /> Export
            </button>
          </div>
          <pre className="bg-cre-dark rounded-lg p-4 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre-wrap">
            {memo}
          </pre>
        </div>
      )}
    </div>
  )
}

// ============ AUTH PAGES ============
function LoginPage({ onLogin }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    if (!form.email || !form.password) return
    setLoading(true)
    try {
      const res = await API.post('/auth/login', form)
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user_id', res.data.user_id)
      onLogin(res.data.user_id)
    } catch (e) {
      setError('Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-cre-dark flex items-center justify-center p-4">
      <div className="cre-card w-full max-w-md">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-lg bg-cre-blue/20 flex items-center justify-center text-cre-blue text-2xl mx-auto mb-3">
            <Icons.Building />
          </div>
          <h1 className="text-2xl font-bold text-white">CRE Suite</h1>
          <p className="text-gray-400 text-sm mt-1">Enterprise Edition</p>
        </div>

        <div className="space-y-4">
          <input type="email" placeholder="Email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
          <input type="password" placeholder="Password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
          {error && <p className="text-cre-red text-xs">{error}</p>}
          <button onClick={handleLogin} disabled={loading} className="cre-btn-primary w-full">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-cre-border text-center">
          <p className="text-gray-400 text-sm">Don't have an account? <button onClick={() => {}} className="text-cre-blue hover:underline">Sign up</button></p>
        </div>
      </div>
    </div>
  )
}

// ============ MAIN APP ============
export default function App() {
  const [page, setPage] = useState('dashboard')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userId = localStorage.getItem('user_id')
    if (token && userId) {
      setUser({ id: userId, username: 'User' })
    }
    setLoading(false)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user_id')
    setUser(null)
    setPage('dashboard')
  }

  if (loading) return <div className="min-h-screen bg-cre-dark flex items-center justify-center"><Icons.Loader /></div>

  if (!user) return <LoginPage onLogin={(userId) => setUser({ id: userId, username: 'User' })} />

  const pages = {
    dashboard: <Dashboard user={user} />,
    properties: <Properties />,
    valuations: <Valuations />,
    rentroll: <RentRoll />,
    memos: <Memos />,
  }

  return (
    <div className="flex h-screen bg-cre-dark overflow-hidden">
      <Sidebar active={page} setActive={setPage} onLogout={handleLogout} />
      <main className="flex-1 overflow-y-auto p-6">
        {pages[page]}
      </main>
    </div>
  )
}
