import { useState, useRef, useCallback } from 'react'

export default function ImageUploader({ onAnalyze, isAnalyzing }) {
    const [preview, setPreview] = useState(null)
    const [file, setFile] = useState(null)
    const [dragover, setDragover] = useState(false)
    const fileInputRef = useRef(null)
    const cameraInputRef = useRef(null)

    const handleFile = useCallback((f) => {
        if (!f) return
        setFile(f)
        const reader = new FileReader()
        reader.onload = (e) => setPreview(e.target.result)
        reader.readAsDataURL(f)
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragover(false)
        const f = e.dataTransfer.files?.[0]
        if (f && f.type.startsWith('image/')) handleFile(f)
    }, [handleFile])

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        setDragover(true)
    }, [])

    const handleDragLeave = useCallback(() => setDragover(false), [])

    const handleAnalyze = () => {
        if (file && onAnalyze) onAnalyze(file)
    }

    const handleClear = () => {
        setFile(null)
        setPreview(null)
    }

    return (
        <div className="card">
            <div className="card-header">
                <span className="icon">📤</span>
                <h2>Upload Eczema Image</h2>
            </div>
            <div className="card-body">
                {!preview ? (
                    <div
                        className={`upload-zone ${dragover ? 'dragover' : ''}`}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onClick={() => fileInputRef.current?.click()}
                        id="upload-zone"
                    >
                        <span className="upload-icon">🔬</span>
                        <div className="upload-title">Drop an image here or click to upload</div>
                        <div className="upload-subtitle">
                            Supports JPG, PNG, WebP • Close-up eczema photos recommended
                        </div>
                        <div className="upload-actions" onClick={(e) => e.stopPropagation()}>
                            <button
                                className="btn btn-primary"
                                onClick={() => fileInputRef.current?.click()}
                                id="upload-btn"
                            >
                                📁 Choose File
                            </button>
                            <button
                                className="btn btn-secondary"
                                onClick={() => cameraInputRef.current?.click()}
                                id="camera-btn"
                            >
                                📷 Use Camera
                            </button>
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            className="upload-input"
                            onChange={(e) => handleFile(e.target.files?.[0])}
                        />
                        <input
                            ref={cameraInputRef}
                            type="file"
                            accept="image/*"
                            capture="environment"
                            className="upload-input"
                            onChange={(e) => handleFile(e.target.files?.[0])}
                        />
                    </div>
                ) : (
                    <div className="preview-container">
                        <img src={preview} alt="Uploaded eczema image" className="preview-image" />
                        <div className="preview-actions">
                            <button
                                className="btn btn-primary"
                                onClick={handleAnalyze}
                                disabled={isAnalyzing}
                                id="analyze-btn"
                            >
                                {isAnalyzing ? (
                                    <>
                                        <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>🔬 Analyze Severity</>
                                )}
                            </button>
                            <button
                                className="btn btn-danger"
                                onClick={handleClear}
                                disabled={isAnalyzing}
                                id="clear-btn"
                            >
                                ✕ Clear
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
