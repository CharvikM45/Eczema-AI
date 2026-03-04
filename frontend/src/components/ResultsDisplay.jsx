import { useState } from 'react'

function ScoreRing({ score, color }) {
    const radius = 65
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (score / 100) * circumference

    return (
        <div className="score-ring">
            <svg viewBox="0 0 160 160">
                <circle className="score-ring-bg" cx="80" cy="80" r={radius} />
                <circle
                    className="score-ring-fill"
                    cx="80"
                    cy="80"
                    r={radius}
                    stroke={color}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                />
            </svg>
            <div className="score-ring-value">
                <span className="score-number" style={{ color }}>{score}</span>
                <span className="score-label">Severity</span>
            </div>
        </div>
    )
}

function MetricBar({ name, value, color }) {
    return (
        <div className="metric">
            <div className="metric-header">
                <span className="metric-name">{name}</span>
                <span className="metric-value">{value.toFixed(1)}</span>
            </div>
            <div className="metric-bar">
                <div
                    className="metric-bar-fill"
                    style={{ width: `${value}%`, background: color || 'var(--primary-500)' }}
                />
            </div>
        </div>
    )
}

export default function ResultsDisplay({ result }) {
    const [heatmapView, setHeatmapView] = useState('heatmap')

    if (!result) return null

    const { severity_score, category, category_color, uv_recommendation, metrics, explanation, heatmap_base64, original_base64, formula } = result

    const categoryClass = category?.toLowerCase()

    return (
        <div className="results-grid" id="results-display">
            {/* Score Card */}
            <div className="result-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <span style={{ fontSize: '1.1rem' }}>📊</span>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Severity Score</h3>
                </div>
                <div className="score-display">
                    <ScoreRing score={severity_score} color={category_color} />
                    <span className={`category-badge ${categoryClass}`}>
                        {category === 'Critical' ? '🔴' : category === 'Severe' ? '🟠' : category === 'Moderate' ? '🟡' : '🟢'}
                        {category}
                    </span>
                </div>
            </div>

            {/* Metrics Card */}
            <div className="result-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <span style={{ fontSize: '1.1rem' }}>📈</span>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Analysis Metrics</h3>
                </div>
                <MetricBar name="Affected Area" value={metrics.affected_area_pct} color="#3b82f6" />
                <MetricBar name="Redness" value={metrics.redness_score} color="#ef4444" />
                <MetricBar name="Texture Roughness" value={metrics.texture_score} color="#f97316" />
                <MetricBar name="Lesion Density" value={metrics.lesion_density} color="#8b5cf6" />
                <MetricBar name="Swelling" value={metrics.swelling_score} color="#ec4899" />
            </div>

            {/* UV Recommendation */}
            <div className="result-card uv-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <span style={{ fontSize: '1.1rem' }}>☀️</span>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>UV Patch Recommendation</h3>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div className="uv-duration">{uv_recommendation.recommended_minutes}</div>
                    <div className="uv-unit">minutes recommended</div>
                    <div className="uv-detail">
                        <span>📐 Dynamic: {uv_recommendation.dynamic_minutes} min</span>
                        <span>•</span>
                        <span>📋 Category: {uv_recommendation.category_minutes} min</span>
                    </div>
                    {uv_recommendation.warning && (
                        <div style={{ marginTop: 12, fontSize: '0.82rem', color: '#f59e0b', fontWeight: 600 }}>
                            {uv_recommendation.warning}
                        </div>
                    )}
                </div>
            </div>

            {/* Heatmap */}
            {(heatmap_base64 || original_base64) && (
                <div className="result-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                        <span style={{ fontSize: '1.1rem' }}>🗺️</span>
                        <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Heatmap Overlay</h3>
                    </div>
                    <div className="heatmap-container">
                        <div className="heatmap-tabs">
                            <button
                                className={`heatmap-tab ${heatmapView === 'heatmap' ? 'active' : ''}`}
                                onClick={() => setHeatmapView('heatmap')}
                            >
                                Heatmap
                            </button>
                            <button
                                className={`heatmap-tab ${heatmapView === 'original' ? 'active' : ''}`}
                                onClick={() => setHeatmapView('original')}
                            >
                                Original
                            </button>
                        </div>
                        <img
                            src={`data:image/jpeg;base64,${heatmapView === 'heatmap' ? heatmap_base64 : original_base64}`}
                            alt={heatmapView === 'heatmap' ? 'Severity heatmap overlay' : 'Original image'}
                            className="heatmap-image"
                        />
                    </div>
                </div>
            )}

            {/* Explanation */}
            <div className="result-card" style={{ gridColumn: '1 / -1' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <span style={{ fontSize: '1.1rem' }}>💡</span>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Assessment Explanation</h3>
                </div>
                <div className="explanation">{explanation}</div>
                {formula && (
                    <div className="formula" style={{ marginTop: 12 }}>
                        {formula}
                    </div>
                )}
            </div>
        </div>
    )
}
