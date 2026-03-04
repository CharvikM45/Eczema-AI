export default function Disclaimer() {
    return (
        <div className="disclaimer" id="disclaimer">
            <div className="disclaimer-title">
                ⚠️ Medical Disclaimer
            </div>
            <p>
                This tool is for <strong>educational and informational purposes only</strong> and does not constitute medical advice, diagnosis, or treatment.
                The severity scores are computed using computer vision algorithms and the EASI-inspired scoring methodology, and
                may not reflect clinical accuracy. UV patch duration recommendations are approximations and should not replace
                professional medical guidance. Always consult a board-certified dermatologist or healthcare provider for proper
                diagnosis and treatment of skin conditions including eczema. Do not delay seeking professional medical advice
                because of information provided by this application.
            </p>
        </div>
    )
}
