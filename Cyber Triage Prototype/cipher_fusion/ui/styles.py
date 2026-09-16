CUSTOM_CSS = """
<style>
/* Modern Dark Glassmorphism & Cyber Theme for CIPHER-FUSION */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Header Styling */
.main-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #090D16 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    border: 1px solid rgba(59, 130, 246, 0.2);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    margin-bottom: 1.5rem;
}

.main-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60A5FA 0%, #A78BFA 50%, #F472B6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}

.main-subtitle {
    color: #94A3B8;
    font-size: 0.9rem;
    margin-top: 0.25rem;
}

/* Metric Cards */
.metric-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15);
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #F8FAFC;
}

.metric-label {
    font-size: 0.8rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.2rem;
}

/* Disclaimer Banner */
.disclaimer-banner {
    background: rgba(220, 38, 38, 0.1);
    border-left: 4px solid #EF4444;
    padding: 0.8rem 1.2rem;
    border-radius: 6px;
    color: #FCA5A5;
    font-size: 0.82rem;
    margin-bottom: 1rem;
}

/* Lead Cards */
.lead-card {
    background: #1E293B;
    border-left: 4px solid #3B82F6;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

.lead-card.high-risk {
    border-left-color: #EF4444;
}

.lead-title {
    font-size: 1rem;
    font-weight: 600;
    color: #F1F5F9;
}

.action-badge {
    background: #1E3A8A;
    color: #93C5FD;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
"""
