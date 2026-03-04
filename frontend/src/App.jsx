import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import ResultsDisplay from './components/ResultsDisplay'
import DatasetBrowser from './components/DatasetBrowser'
import Disclaimer from './components/Disclaimer'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export default function App() {
    const [view, setView] = useState('analyzer')
    const [result, setResult] = useState(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [error, setError] = useState(null)

    const handleAnalyze = async (file) => {
        setIsAnalyzing(true)
        setError(null)
        setResult(null)

        try {
            const formData = new FormData()
            formData.append('file', file)

            const res = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                throw new Error(errData.detail || `Analysis failed (${res.status})`)
            }

            const data = await res.json()
            setResult(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setIsAnalyzing(false)
        }
    }

    return (
        <div className="app">
            {/* Header */}
            <header className="header">
                <div className="header-inner">
                    <div className="logo">
                        <div className="logo-icon">🔬</div>
                        <div>
                            <h1>Eczema Severity Analyzer</h1>
                            <div className="logo-subtitle">AI-Powered Skin Analysis</div>
                        </div>
                    </div>

                    <nav className="nav" id="main-nav">
                        <button
                            className={`nav-btn ${view === 'analyzer' ? 'active' : ''}`}
                            onClick={() => setView('analyzer')}
                            id="nav-analyzer"
                        >
                            🔬 Analyzer
                        </button>
                        <button
                            className={`nav-btn ${view === 'dataset' ? 'active' : ''}`}
                            onClick={() => setView('dataset')}
                            id="nav-dataset"
                        >
                            📊 Dataset Results
                        </button>
                    </nav>
                </div>
            </header>

            {/* Main Content */}
            <main className="main">
                {view === 'analyzer' && (
                    <>
                        {error && (
                            <div className="error-banner" style={{ marginBottom: 20 }}>
                                ⚠️ {error}
                                <button
                                    className="btn btn-secondary"
                                    style={{ marginLeft: 'auto', padding: '4px 12px', fontSize: '0.78rem' }}
                                    onClick={() => setError(null)}
                                >
                                    Dismiss
                                </button>
                            </div>
                        )}

                        <div className="analyzer-layout">
                            <div className="analyzer-left">
                                <ImageUploader onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
                            </div>
                            <div className="analyzer-right">
                                {isAnalyzing && (
                                    <div className="loading-container">
                                        <div className="spinner" />
                                        <span>Analyzing eczema severity...</span>
                                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                            Computing affected area, redness, texture, lesion density, and swelling metrics
                                        </span>
                                    </div>
                                )}
                                {result && !isAnalyzing && (
                                    <ResultsDisplay result={result} />
                                )}
                                {!result && !isAnalyzing && (
                                    <div className="card">
                                        <div className="card-body" style={{ textAlign: 'center', padding: '48px 24px' }}>
                                            <span style={{ fontSize: '3rem', display: 'block', marginBottom: 16, opacity: 0.4 }}>🔬</span>
                                            <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                                                Upload an eczema image to get started.<br />
                                                The analyzer will compute severity using the EASI-inspired formula.
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                )}

                {view === 'dataset' && <DatasetBrowser />}

                <Disclaimer />
            </main>
        </div>
    )
}
