import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FiCheckCircle, FiXCircle, FiShield, FiUser, FiCopy,
    FiLoader, FiAlertTriangle, FiZap, FiSearch, FiCpu, FiDownload
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip } from 'chart.js';
import axios from 'axios';
import API_BASE from '../services/api';

ChartJS.register(ArcElement, Tooltip);

// ─── Helpers ────────────────────────────────────────────────────────────────

const StepRow = ({ step, label, status }) => (
    <div className="flex items-center gap-3 py-2">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all
            ${status === 'done' ? 'bg-indigo-600 text-white' :
                status === 'checking' ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 animate-pulse' :
                    'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
            {step}
        </div>
        <span className={`text-sm font-medium flex-1
            ${status === 'done' ? 'text-gray-800 dark:text-gray-100' :
                status === 'checking' ? 'text-indigo-600 dark:text-indigo-400 animate-pulse' :
                    'text-gray-300 dark:text-gray-600'}`}>
            {label}
        </span>
        {status === 'checking' && <FiLoader className="w-3.5 h-3.5 text-indigo-500 animate-spin" />}
        {status === 'done' && <FiCheckCircle className="w-3.5 h-3.5 text-indigo-500" />}
    </div>
);

const ProgressBar = ({ score, color = 'bg-orange-400', label, sublabel }) => {
    const pct = Math.round(Math.min(Math.max(score ?? 0, 0), 100));
    return (
        <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-400 mb-1.5">
                <span>{label}</span>
                <span className="font-bold" style={{ color: 'inherit' }}>{pct}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <motion.div
                    className={`h-2 rounded-full ${color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.9, ease: 'easeOut' }}
                />
            </div>
            {sublabel && <p className="text-xs text-gray-400 mt-1">{sublabel}</p>}
        </div>
    );
};

// ─── Confidence Gauge (Doughnut) ─────────────────────────────────────────────
const ConfidenceGauge = ({ score }) => {
    const pct = Math.round(Math.min(Math.max(score ?? 0, 0), 100));
    const remaining = 100 - pct;

    const color =
        pct >= 75 ? '#10b981' :   // green
        pct >= 40 ? '#f59e0b' :   // amber
                    '#ef4444';    // red

    const data = {
        datasets: [{
            data: [pct, remaining],
            backgroundColor: [color, '#1f293720'],
            borderWidth: 0,
            circumference: 220,
            rotation: -110,
        }],
    };

    const options = {
        cutout: '78%',
        plugins: { tooltip: { enabled: false } },
        animation: { animateRotate: true, duration: 900 },
    };

    return (
        <div className="relative w-32 h-28 mx-auto">
            <Doughnut data={data} options={options} />
            <div className="absolute inset-0 flex flex-col items-center justify-center mt-3">
                <span className="text-2xl font-black" style={{ color }}>{pct}</span>
                <span className="text-xs text-gray-400 font-medium">/ 100</span>
            </div>
        </div>
    );
};

// ─── Risk Level Badge ────────────────────────────────────────────────────────
const RiskBadge = ({ level }) => {
    const styles = {
        Low:    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-300',
        Medium: 'bg-amber-100   text-amber-700   dark:bg-amber-900/40   dark:text-amber-300   border border-amber-300',
        High:   'bg-red-100     text-red-700     dark:bg-red-900/40     dark:text-red-300     border border-red-300',
    };
    const icons = { Low: '🟢', Medium: '🟠', High: '🔴' };
    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold ${styles[level] ?? styles.Medium}`}>
            {icons[level] ?? '⚪'} Risk: {level ?? 'Unknown'}
        </span>
    );
};

// ─── Layer Card wrapper ──────────────────────────────────────────────────────
const LayerCard = ({ delay, accentColor, labelBg, labelText, labelCode, title, subtitle, badge, children }) => (
    <motion.div
        initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay }}
        className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-sm relative overflow-hidden"
    >
        <div className={`absolute top-0 left-0 w-1 h-full ${accentColor} rounded-l-xl`} />
        <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
                <div className={`p-2 ${labelBg} rounded-lg`}>
                    <span className={`${labelText} font-mono font-bold text-sm`}>{labelCode}</span>
                </div>
                <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h3>
                    <p className="text-xs text-gray-400">{subtitle}</p>
                </div>
            </div>
            {badge}
        </div>
        {children}
    </motion.div>
);

// ─── Main Component ──────────────────────────────────────────────────────────
const LayeredVerificationCard = ({ result, isAdmin = false }) => {
    const [stepStatus, setStepStatus] = useState(['checking', 'pending', 'pending', 'pending', 'pending']);

    useEffect(() => {
        if (!result) return;
        const timings = [600, 700, 1400, 1500, 2200, 2300, 3000, 3100, 3800];
        const updates = [
            () => setStepStatus(['done', 'pending', 'pending', 'pending', 'pending']),
            () => setStepStatus(['done', 'checking', 'pending', 'pending', 'pending']),
            () => setStepStatus(['done', 'done', 'pending', 'pending', 'pending']),
            () => setStepStatus(['done', 'done', 'checking', 'pending', 'pending']),
            () => setStepStatus(['done', 'done', 'done', 'pending', 'pending']),
            () => setStepStatus(['done', 'done', 'done', 'checking', 'pending']),
            () => setStepStatus(['done', 'done', 'done', 'done', 'pending']),
            () => setStepStatus(['done', 'done', 'done', 'done', 'checking']),
            () => setStepStatus(['done', 'done', 'done', 'done', 'done']),
        ];
        const timers = timings.map((t, i) => setTimeout(updates[i], t));
        return () => timers.forEach(clearTimeout);
    }, [result]);

    if (!result) return null;

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        toast.success('Copied to clipboard');
    };

    const [downloading, setDownloading] = useState(false);
    const downloadReport = async () => {
        setDownloading(true);
        const toastId = toast.loading('Generating PDF report...');
        try {
            const token = localStorage.getItem('token');
            const res = await axios.post(`${API_BASE}/report/generate`, result, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `forensic_report_${Date.now()}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            toast.success('Report downloaded!', { id: toastId });
        } catch (e) {
            toast.error('Report generation failed.', { id: toastId });
        } finally {
            setDownloading(false);
        }
    };

    const wm = result.watermark_matched ?? false;
    const hm = result.hash_matched ?? false;
    const sm = result.similarity_matched ?? false;
    const td = result.tamper_detected ?? false;

    const tamperPct = Math.round((result.tamper_probability ?? 0) * 100);
    const simPct = Math.round(result.similarity_score ?? 0);
    const verdict = result.final_verdict ?? 'External Media';
    const riskLevel = result.risk_level ?? 'High';
    const confScore = result.confidence_score ?? 0;

    // Card border
    const borderBg =
        (wm && hm) ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10' :
        wm         ? 'border-green-500   bg-green-50   dark:bg-green-900/10' :
        hm         ? 'border-blue-500    bg-blue-50    dark:bg-blue-900/10' :
        sm         ? 'border-orange-400  bg-orange-50  dark:bg-orange-900/10' :
        td         ? 'border-red-500     bg-red-50     dark:bg-red-900/10' :
                     'border-yellow-400  bg-yellow-50  dark:bg-yellow-900/10';

    const verdictColor =
        verdict === 'Verified User'       ? 'text-emerald-600 dark:text-emerald-400' :
        verdict === 'Identical Reupload'  ? 'text-blue-600 dark:text-blue-400' :
        verdict === 'Derived Media'       ? 'text-orange-500 dark:text-orange-400' :
        verdict === 'Tampered Suspicious' ? 'text-red-600 dark:text-red-400' :
                                            'text-yellow-600 dark:text-yellow-500';

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className={`w-full rounded-2xl shadow-xl overflow-hidden border-2 ${borderBg}`}
        >
            <div className="p-6 md:p-8 space-y-5">

                {/* Header */}
                <div className="flex items-center gap-3 flex-wrap">
                    <FiShield className="w-7 h-7 text-gray-700 dark:text-gray-200" />
                    <h2 className="text-xl font-bold text-gray-800 dark:text-white">Forensic Intelligence Report</h2>
                    {wm && hm && (
                        <span className="ml-auto flex items-center gap-1 text-xs font-bold bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 px-2.5 py-1 rounded-full">
                            <FiZap className="w-3 h-3" /> FULL MATCH
                        </span>
                    )}
                    {td && !wm && !hm && (
                        <span className="ml-auto flex items-center gap-1 text-xs font-bold bg-red-100 dark:bg-red-900/40 text-red-600 px-2.5 py-1 rounded-full">
                            <FiAlertTriangle className="w-3 h-3" /> TAMPERED
                        </span>
                    )}
                </div>

                {/* Progress Steps */}
                <div className="bg-white dark:bg-gray-800/60 rounded-xl px-5 py-1 border border-gray-100 dark:border-gray-700">
                    {[
                        'Checking Steganographic Watermark (AES-256)...',
                        'Checking SHA-256 Hash (original + watermarked)...',
                        'Checking Perceptual / Semantic Similarity...',
                        'Running ML Tamper Detection...',
                        'Aggregating Risk Score...',
                    ].map((label, i) => (
                        <div key={i}>
                            <StepRow step={i + 1} label={label} status={stepStatus[i]} />
                            {i < 4 && <div className="border-t border-gray-100 dark:border-gray-700/50" />}
                        </div>
                    ))}
                </div>

                {/* ── LAYER 1: Watermark ── */}
                <LayerCard
                    delay={0.2}
                    accentColor="bg-green-500"
                    labelBg="bg-green-100 dark:bg-green-900/50"
                    labelText="text-green-600 dark:text-green-400"
                    labelCode="L1"
                    title="Hidden Watermark"
                    subtitle="LSB Steganography · AES-256 Encrypted"
                    badge={wm
                        ? <span className="flex items-center gap-1 text-green-600 font-bold bg-green-100 dark:bg-green-900/50 px-3 py-1 rounded-full text-xs"><FiCheckCircle /> Detected</span>
                        : <span className="flex items-center gap-1 text-gray-400 bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full text-xs"><FiXCircle /> Not Found</span>}
                >
                    <AnimatePresence>
                        {wm && (
                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                                className="mt-2 pl-3 border-l-2 border-green-100 dark:border-green-800 space-y-1.5">
                                {result.uploader_email && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                        <FiUser className="w-4 h-4 flex-shrink-0" />
                                        <span className="font-mono">{result.uploader_email}</span>
                                    </div>
                                )}
                                {result.original_user_id && (
                                    <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
                                        <span className="truncate">ID: {result.original_user_id}</span>
                                        {isAdmin && (
                                            <button onClick={() => copyToClipboard(result.original_user_id)}
                                                className="hover:text-indigo-500 transition-colors flex-shrink-0"><FiCopy /></button>
                                        )}
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </LayerCard>

                {/* ── LAYER 2: Hash ── */}
                <LayerCard
                    delay={0.3}
                    accentColor="bg-blue-500"
                    labelBg="bg-blue-100 dark:bg-blue-900/50"
                    labelText="text-blue-600 dark:text-blue-400"
                    labelCode="L2"
                    title="Cryptographic Hash"
                    subtitle="SHA-256 · Matches original or watermarked copy"
                    badge={hm
                        ? <span className="flex items-center gap-1 text-blue-600 font-bold bg-blue-100 dark:bg-blue-900/50 px-3 py-1 rounded-full text-xs"><FiCheckCircle /> Match Found</span>
                        : <span className="flex items-center gap-1 text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-1 rounded-full text-xs"><FiXCircle /> No Match</span>}
                >
                    <AnimatePresence>
                        {hm && result.original_upload_date && (
                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                                className="mt-2 pl-3 border-l-2 border-blue-100 dark:border-blue-800 space-y-1.5">
                                {result.uploader_email && !wm && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                        <FiUser className="w-4 h-4" />
                                        <span className="font-mono">{result.uploader_email}</span>
                                    </div>
                                )}
                                <p className="text-xs text-gray-400 font-mono">
                                    Originally uploaded: {new Date(result.original_upload_date).toLocaleString()}
                                </p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </LayerCard>

                {/* ── LAYER 3: Similarity ── */}
                <LayerCard
                    delay={0.4}
                    accentColor="bg-orange-400"
                    labelBg="bg-orange-100 dark:bg-orange-900/40"
                    labelText="text-orange-600 dark:text-orange-400"
                    labelCode="L3"
                    title="Similarity Detection"
                    subtitle="pHash (image) · TF-IDF Cosine (text)"
                    badge={sm
                        ? <span className="flex items-center gap-1 text-orange-600 font-bold bg-orange-100 dark:bg-orange-900/40 px-3 py-1 rounded-full text-xs"><FiAlertTriangle /> Similar Found</span>
                        : <span className="flex items-center gap-1 text-gray-400 bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full text-xs"><FiXCircle /> No Similar</span>}
                >
                    <ProgressBar
                        score={simPct}
                        color={simPct >= 90 ? 'bg-red-500' : simPct >= 75 ? 'bg-orange-400' : 'bg-yellow-400'}
                        label="Similarity Score"
                    />
                    {sm && result.similarity_matched_media_id && (
                        <div className="flex items-center gap-2 text-xs text-gray-400 font-mono mt-2">
                            <span className="truncate">Matched: {result.similarity_matched_media_id}</span>
                            {isAdmin && (
                                <button onClick={() => copyToClipboard(result.similarity_matched_media_id)}
                                    className="hover:text-orange-500 transition-colors flex-shrink-0"><FiCopy /></button>
                            )}
                        </div>
                    )}
                </LayerCard>

                {/* ── LAYER 4: ML Tamper Detection ── */}
                <LayerCard
                    delay={0.5}
                    accentColor="bg-purple-500"
                    labelBg="bg-purple-100 dark:bg-purple-900/40"
                    labelText="text-purple-600 dark:text-purple-400"
                    labelCode="L4"
                    title="ML Tamper Detection"
                    subtitle={`${result.tamper_method === 'ml' ? 'MobileNetV2 · Deep Learning' : 'Heuristic · Noise & Edge Analysis'}`}
                    badge={td
                        ? <span className="flex items-center gap-1 text-red-600 font-bold bg-red-100 dark:bg-red-900/40 px-3 py-1 rounded-full text-xs"><FiAlertTriangle /> Tampered</span>
                        : <span className="flex items-center gap-1 text-emerald-600 font-bold bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 rounded-full text-xs"><FiCheckCircle /> Authentic</span>}
                >
                    <ProgressBar
                        score={tamperPct}
                        color={tamperPct >= 60 ? 'bg-red-500' : tamperPct >= 35 ? 'bg-amber-400' : 'bg-emerald-400'}
                        label="Tamper Probability"
                        sublabel={td ? 'Significant manipulation detected' : 'File appears authentic'}
                    />
                </LayerCard>

                {/* ── LAYER 5: Risk Aggregation ── */}
                <motion.div
                    initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 }}
                    className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-sm relative overflow-hidden"
                >
                    <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500 rounded-l-xl" />
                    <div className="flex items-center gap-2 mb-4">
                        <div className="p-2 bg-indigo-100 dark:bg-indigo-900/40 rounded-lg">
                            <FiCpu className="text-indigo-600 dark:text-indigo-400 w-4 h-4" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Risk Aggregation Engine</h3>
                            <p className="text-xs text-gray-400">WM 50% + Hash 30% + Sim 10% + ML 10%</p>
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row items-center justify-around gap-4">
                        <div className="text-center">
                            <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-2">Confidence Score</p>
                            <ConfidenceGauge score={confScore} />
                        </div>
                        <div className="text-center space-y-3">
                            <div>
                                <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">Final Verdict</p>
                                <p className={`text-lg font-black ${verdictColor}`}>{verdict}</p>
                            </div>
                            <RiskBadge level={riskLevel} />
                        </div>
                    </div>
                </motion.div>

                {/* Download Report Button */}
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
                    className="pt-2"
                >
                    <button
                        onClick={downloadReport}
                        disabled={downloading}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-bold rounded-xl shadow-md transition-all"
                    >
                        {downloading
                            ? <><FiLoader className="animate-spin w-4 h-4" /> Generating PDF...</>
                            : <><FiDownload className="w-4 h-4" /> Download Forensic Report (PDF)</>
                        }
                    </button>
                </motion.div>

                {/* Footer */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-3 text-center text-xs text-gray-400 font-mono">
                    SHA-256: {result.hashed?.substring(0, 24)}...
                    &nbsp;·&nbsp;
                    {new Date(result.verified_at).toLocaleTimeString()}
                </div>
            </div>
        </motion.div>
    );
};

export default LayeredVerificationCard;
