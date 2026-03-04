import { useState, useEffect, useMemo } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const ITEMS_PER_PAGE = 24

export default function DatasetBrowser() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [filter, setFilter] = useState('All')
    const [search, setSearch] = useState('')
    const [sortBy, setSortBy] = useState('score-desc')
    const [page, setPage] = useState(1)

    useEffect(() => {
        fetchDatasetResults()
    }, [])

    const fetchDatasetResults = async () => {
        try {
            setLoading(true)
            const res = await fetch(`${API_BASE}/dataset-results/summary`)
            if (!res.ok) throw new Error('Failed to load dataset results')
            const json = await res.json()
            setData(json)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const filtered = useMemo(() => {
        if (!data?.results) return []
        let items = [...data.results]

        // Filter by category
        if (filter !== 'All') {
            items = items.filter(r => r.category === filter)
        }

        // Search by filename
        if (search.trim()) {
            const q = search.toLowerCase()
            items = items.filter(r => r.filename.toLowerCase().includes(q))
        }

        // Sort
        switch (sortBy) {
            case 'score-desc':
                items.sort((a, b) => b.severity_score - a.severity_score)
                break
            case 'score-asc':
                items.sort((a, b) => a.severity_score - b.severity_score)
                break
            case 'name':
                items.sort((a, b) => a.filename.localeCompare(b.filename))
                break
        }

        return items
    }, [data, filter, search, sortBy])

    const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
    const paginated = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE)

    // Reset page when filters change
    useEffect(() => { setPage(1) }, [filter, search, sortBy])

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner" />
                <span>Loading dataset analysis...</span>
            </div>
        )
    }

    if (error) {
        return <div className="error-banner">⚠️ {error}</div>
    }

    if (!data) return null

    const { statistics } = data
    const categories = ['All', 'Mild', 'Moderate', 'Severe', 'Critical']
    const categoryColors = { Mild: 'var(--severity-mild)', Moderate: 'var(--severity-moderate)', Severe: 'var(--severity-severe)', Critical: 'var(--severity-critical)' }
    const dist = statistics.category_distribution || {}
    const maxDist = Math.max(...Object.values(dist), 1)

    return (
        <div id="dataset-browser">
            {/* Statistics */}
            <div className="dataset-header">
                <div className="dataset-stats">
                    <div className="stat-pill">
                        📊 <strong>{data.total_images}</strong> images analyzed
                    </div>
                    <div className="stat-pill">
                        📈 Mean: <strong>{statistics.mean_score}</strong>
                    </div>
                    <div className="stat-pill">
                        📉 Range: <strong>{statistics.min_score}–{statistics.max_score}</strong>
                    </div>
                </div>
            </div>

            {/* Distribution */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <span className="icon">📊</span>
                    <h2>Severity Distribution</h2>
                </div>
                <div className="card-body">
                    <div className="distribution" style={{ height: 100, marginBottom: 24 }}>
                        {['Mild', 'Moderate', 'Severe', 'Critical'].map(cat => {
                            const count = dist[cat] || 0
                            const height = (count / maxDist) * 100
                            return (
                                <div
                                    key={cat}
                                    className="distribution-bar"
                                    style={{
                                        height: `${height}%`,
                                        background: categoryColors[cat],
                                        opacity: 0.85,
                                    }}
                                >
                                    <span className="distribution-bar-count">{count}</span>
                                    <span className="distribution-bar-label">{cat}</span>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="dataset-controls" style={{ marginBottom: 20 }}>
                {categories.map(cat => (
                    <button
                        key={cat}
                        className={`filter-btn ${filter === cat ? 'active' : ''}`}
                        onClick={() => setFilter(cat)}
                    >
                        {cat !== 'All' && (
                            <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: categoryColors[cat], marginRight: 6 }} />
                        )}
                        {cat}
                        {cat !== 'All' && dist[cat] ? ` (${dist[cat]})` : ''}
                    </button>
                ))}

                <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="filter-btn"
                    style={{ cursor: 'pointer' }}
                >
                    <option value="score-desc">Score ↓</option>
                    <option value="score-asc">Score ↑</option>
                    <option value="name">Name A-Z</option>
                </select>

                <input
                    type="text"
                    className="search-input"
                    placeholder="🔍 Search filename..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {/* Results count */}
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                Showing {paginated.length} of {filtered.length} results
            </div>

            {/* Grid */}
            <div className="dataset-grid">
                {paginated.map((item, i) => {
                    const catClass = item.category?.toLowerCase()
                    return (
                        <div key={item.filename} className="dataset-item" style={{ animationDelay: `${i * 0.03}s` }}>
                            <div className="dataset-item-header">
                                <span className="dataset-item-filename" title={item.filename}>
                                    {item.filename}
                                </span>
                                <span className={`category-badge ${catClass}`} style={{ fontSize: '0.68rem', padding: '3px 10px' }}>
                                    {item.category}
                                </span>
                            </div>
                            <div className="dataset-item-score">
                                <span
                                    className="dataset-item-score-value"
                                    style={{ color: item.category_color }}
                                >
                                    {item.severity_score}
                                </span>
                                <div style={{ flex: 1 }}>
                                    <div className="metric-bar" style={{ marginBottom: 4 }}>
                                        <div
                                            className="metric-bar-fill"
                                            style={{ width: `${item.severity_score}%`, background: item.category_color }}
                                        />
                                    </div>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                        UV: {item.uv_recommendation?.recommended_minutes} min
                                    </div>
                                </div>
                            </div>
                            <div className="dataset-item-metrics">
                                <div className="dataset-item-metric">
                                    <span>Area</span>
                                    <span>{item.metrics.affected_area_pct}%</span>
                                </div>
                                <div className="dataset-item-metric">
                                    <span>Redness</span>
                                    <span>{item.metrics.redness_score}</span>
                                </div>
                                <div className="dataset-item-metric">
                                    <span>Texture</span>
                                    <span>{item.metrics.texture_score}</span>
                                </div>
                                <div className="dataset-item-metric">
                                    <span>Lesion</span>
                                    <span>{item.metrics.lesion_density}</span>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        className="pagination-btn"
                        disabled={page <= 1}
                        onClick={() => setPage(p => p - 1)}
                    >
                        ← Previous
                    </button>
                    <span className="pagination-info">
                        Page {page} of {totalPages}
                    </span>
                    <button
                        className="pagination-btn"
                        disabled={page >= totalPages}
                        onClick={() => setPage(p => p + 1)}
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    )
}
