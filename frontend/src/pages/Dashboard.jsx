import { useNavigate } from 'react-router-dom';
import { useEffect, useState, useCallback, useRef } from 'react';
import {
    FiUploadCloud, FiShield, FiDatabase, FiFileText, FiDownload,
    FiTrash2, FiImage, FiLock, FiCheckCircle, FiX, FiPlus
} from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';
import { uploadMedia } from '../services/api';
import API_BASE from '../services/api';


// ─── Inline Upload Panel ────────────────────────────────────────────────────
const InlineUploader = ({ onSuccess, onClose }) => {
    const [file, setFile] = useState(null);
    const [mediaType, setMediaType] = useState('image');
    const [preview, setPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const fileRef = useRef();

    const handleFile = (f) => {
        if (!f) return;
        if (mediaType === 'image' && !f.type.startsWith('image/')) {
            toast.error('Please select an image file'); return;
        }
        if (mediaType === 'text' && !f.name.endsWith('.txt') && f.type !== 'text/plain') {
            toast.error('Please select a .txt file'); return;
        }
        setFile(f);
        if (mediaType === 'image') {
            setPreview(URL.createObjectURL(f));
        } else {
            const reader = new FileReader();
            reader.onload = e => setPreview(e.target.result?.substring(0, 180) + '…');
            reader.readAsText(f);
        }
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const f = e.dataTransfer.files[0];
        if (f) handleFile(f);
    }, [mediaType]);

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        try {
            const res = await uploadMedia(file, mediaType);
            toast.success('Uploaded & watermarked successfully!');
            onSuccess(res.data);
            setFile(null); setPreview(null);
        } catch (err) {
            if (err.response?.status === 409) {
                toast.error('Duplicate — this file already exists in the system.');
            } else {
                toast.error(err.response?.data?.detail || 'Upload failed');
            }
        } finally {
            setUploading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 mb-8"
        >
            <div className="flex justify-between items-center mb-5">
                <h3 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                    <FiUploadCloud className="text-indigo-500" /> New Secure Upload
                </h3>
                <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                >
                    <FiX />
                </button>
            </div>

            {/* Type Toggle */}
            <div className="flex gap-3 mb-5">
                {['image', 'text'].map(t => (
                    <button
                        key={t}
                        onClick={() => { setMediaType(t); setFile(null); setPreview(null); }}
                        className={`flex-1 py-2.5 rounded-xl font-semibold text-sm transition-all capitalize flex items-center justify-center gap-2
                            ${mediaType === t
                                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200 dark:shadow-none'
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
                    >
                        {t === 'image' ? <FiImage className="w-4 h-4" /> : <FiFileText className="w-4 h-4" />}
                        {t}
                    </button>
                ))}
            </div>

            {/* Drop Zone */}
            <div
                onDragOver={e => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                    ${file
                        ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:border-indigo-400 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}
            >
                <input
                    ref={fileRef}
                    type="file"
                    className="hidden"
                    accept={mediaType === 'image' ? 'image/*' : '.txt,text/plain'}
                    onChange={e => handleFile(e.target.files[0])}
                />
                {file ? (
                    <div className="flex flex-col items-center gap-3">
                        {preview && mediaType === 'image' ? (
                            <img src={preview} alt="preview" className="max-h-36 rounded-lg shadow-sm object-contain" />
                        ) : preview ? (
                            <div className="text-left bg-white dark:bg-gray-900 p-3 rounded-lg border border-gray-100 dark:border-gray-700 font-mono text-xs text-gray-600 dark:text-gray-300 max-w-full overflow-hidden">
                                {preview}
                            </div>
                        ) : null}
                        <p className="text-sm font-medium text-indigo-700 dark:text-indigo-300">{file.name}</p>
                        <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-3 text-gray-400">
                        <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-full">
                            <FiUploadCloud className="w-8 h-8" />
                        </div>
                        <div>
                            <p className="font-medium text-gray-600 dark:text-gray-300">Drag & drop or click to browse</p>
                            <p className="text-sm mt-1">
                                {mediaType === 'image' ? 'JPG, PNG · Max 10MB' : '.TXT · Max 10MB'}
                            </p>
                        </div>
                    </div>
                )}
            </div>

            <AnimatePresence>
                {file && (
                    <motion.button
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        onClick={handleUpload}
                        disabled={uploading}
                        className="w-full mt-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-70"
                    >
                        {uploading ? (
                            <>
                                <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                                Encrypting & Watermarking...
                            </>
                        ) : (
                            <><FiLock /> Secure Upload & Watermark</>
                        )}
                    </motion.button>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// ─── Media Card ─────────────────────────────────────────────────────────────
const MediaCard = ({ item, onDelete }) => {
    const [downloading, setDownloading] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [imgSrc, setImgSrc] = useState(item.url || null); // try Cloudinary first
    const [imgFailed, setImgFailed] = useState(false);

    // If Cloudinary URL is missing or broken, load from download endpoint as blob
    useEffect(() => {
        if (item.media_type !== 'image') return;
        if (item.url) return; // Cloudinary available, use it
        // No Cloudinary URL: fetch via download endpoint
        const token = localStorage.getItem('token');
        axios.get(`${API_BASE}/my-uploads/${item.media_id}/download`, {
            headers: { Authorization: `Bearer ${token}` },
            responseType: 'blob'
        }).then(res => {
            const blobUrl = URL.createObjectURL(res.data);
            setImgSrc(blobUrl);
        }).catch(() => {
            setImgSrc(null);
        });
    }, [item.media_id, item.url, item.media_type]);

    const handleDownload = async () => {
        setDownloading(true);
        const token = localStorage.getItem('token');
        try {
            const res = await axios.get(`${API_BASE}/my-uploads/${item.media_id}/download`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            });
            const ext = item.media_type === 'image' ? 'png' : 'txt';
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `watermarked_${item.media_id}.${ext}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            toast.success('Watermarked file downloaded!');
        } catch {
            toast.error('Download failed — file may not be on the server.');
        } finally {
            setDownloading(false);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm('Delete this file permanently? This cannot be undone.')) return;
        setDeleting(true);
        const token = localStorage.getItem('token');
        try {
            await axios.delete(`${API_BASE}/my-uploads/${item.media_id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            toast.success('File deleted.');
            onDelete(item.media_id);
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Delete failed.');
        } finally {
            setDeleting(false);
        }
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden group hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
        >
            {/* Thumbnail */}
            <div className="h-44 bg-gray-50 dark:bg-gray-900 flex items-center justify-center relative overflow-hidden">
                {item.media_type === 'image' && imgSrc && !imgFailed ? (
                    <img
                        src={imgSrc}
                        alt="Upload"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={() => setImgFailed(true)}
                    />
                ) : item.media_type === 'image' ? (
                    <div className="flex flex-col items-center text-gray-300 dark:text-gray-600">
                        <FiImage className="w-10 h-10 mb-1" />
                        <span className="text-xs">Image</span>
                    </div>
                ) : (
                    <div className="flex flex-col items-center text-gray-300 dark:text-gray-600">
                        <FiFileText className="w-10 h-10 mb-1" />
                        <span className="text-xs">Text File</span>
                    </div>
                )}

                {/* Badges */}
                <div className="absolute top-2 left-2 flex gap-1 flex-wrap">
                    <span className="bg-black/60 text-white text-[10px] px-2 py-0.5 rounded-full font-semibold backdrop-blur-sm uppercase">
                        {item.media_type}
                    </span>
                    {item.watermark_present && (
                        <span className="bg-green-500/90 text-white text-[10px] px-2 py-0.5 rounded-full font-semibold backdrop-blur-sm flex items-center gap-0.5">
                            <FiShield className="w-2.5 h-2.5" /> WM
                        </span>
                    )}
                </div>
            </div>

            {/* Info */}
            <div className="p-4">
                <p className="text-xs font-mono text-gray-400 truncate mb-2" title={item.media_id}>
                    {item.media_id.substring(0, 18)}…
                </p>
                <div className="flex items-center justify-between gap-1">
                    <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-md">
                        {new Date(item.uploaded_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' })}
                    </span>
                    <div className="flex items-center gap-1.5">
                        {item.watermark_present && (
                            <FiCheckCircle className="text-green-500 w-3.5 h-3.5 flex-shrink-0" title="Watermarked" />
                        )}
                        <button
                            onClick={handleDownload}
                            disabled={downloading || deleting}
                            className="p-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-800/50 transition-colors disabled:opacity-40"
                            title="Download watermarked file"
                        >
                            {downloading
                                ? <span className="animate-spin block h-3 w-3 border border-indigo-500 border-t-transparent rounded-full" />
                                : <FiDownload className="w-3.5 h-3.5" />}
                        </button>
                        <button
                            onClick={handleDelete}
                            disabled={deleting || downloading}
                            className="p-1.5 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-800/30 transition-colors disabled:opacity-40"
                            title="Delete file"
                        >
                            {deleting
                                ? <span className="animate-spin block h-3 w-3 border border-red-400 border-t-transparent rounded-full" />
                                : <FiTrash2 className="w-3.5 h-3.5" />}
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

// ─── Dashboard ───────────────────────────────────────────────────────────────
const Dashboard = () => {
    const navigate = useNavigate();
    const [uploads, setUploads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showUploader, setShowUploader] = useState(false);

    const fetchUploads = async () => {
        const token = localStorage.getItem('token');
        if (!token) { navigate('/login'); return; }
        try {
            const res = await axios.get(`${API_BASE}/my-uploads`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setUploads(res.data);
        } catch (err) {
            console.error('Failed to fetch uploads:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchUploads(); }, []);

    const handleUploadSuccess = (newItem) => {
        // Prepend newly uploaded item and close uploader
        setUploads(prev => [newItem, ...prev]);
        setShowUploader(false);
    };

    const handleDelete = (mediaId) => {
        setUploads(prev => prev.filter(u => u.media_id !== mediaId));
    };

    const totalImages = uploads.filter(u => u.media_type === 'image').length;
    const totalTexts = uploads.filter(u => u.media_type === 'text').length;
    const watermarked = uploads.filter(u => u.watermark_present).length;

    const stats = [
        { label: 'Total Files', value: uploads.length, icon: FiDatabase, color: 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400' },
        { label: 'Watermarked', value: watermarked, icon: FiShield, color: 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400' },
        { label: 'Images / Texts', value: `${totalImages} / ${totalTexts}`, icon: FiImage, color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400' },
    ];

    return (
        <div className="p-6 md:p-8 max-w-screen-xl mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-1">My Media</h1>
                        <p className="text-gray-500 dark:text-gray-400 text-sm">Manage your encrypted, watermarked files.</p>
                    </div>
                    <button
                        onClick={() => setShowUploader(v => !v)}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold shadow-md transition-all
                            ${showUploader
                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
                                : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200 dark:shadow-none'}`}
                    >
                        {showUploader ? <><FiX /> Cancel</> : <><FiPlus /> New Upload</>}
                    </button>
                </div>

                {/* Inline Uploader */}
                <AnimatePresence>
                    {showUploader && (
                        <InlineUploader
                            onSuccess={handleUploadSuccess}
                            onClose={() => setShowUploader(false)}
                        />
                    )}
                </AnimatePresence>

                {/* Stats */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
                    {stats.map((s, i) => (
                        <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center gap-4">
                            <div className={`p-3.5 rounded-xl ${s.color}`}>
                                <s.icon className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">{s.value}</p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">{s.label}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Media Grid */}
                <div className="flex items-center justify-between mb-5">
                    <h2 className="text-lg font-bold text-gray-800 dark:text-white">
                        Uploaded Files
                        {!loading && uploads.length > 0 && (
                            <span className="ml-2 text-sm font-normal text-gray-400">({uploads.length})</span>
                        )}
                    </h2>
                </div>

                {loading ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5">
                        {[...Array(6)].map((_, i) => (
                            <div key={i} className="bg-gray-100 dark:bg-gray-800 rounded-2xl h-52 animate-pulse" />
                        ))}
                    </div>
                ) : uploads.length > 0 ? (
                    <motion.div layout className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5">
                        <AnimatePresence>
                            {uploads.map((item) => (
                                <MediaCard
                                    key={item.media_id}
                                    item={item}
                                    onDelete={handleDelete}
                                />
                            ))}
                        </AnimatePresence>
                    </motion.div>
                ) : (
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-14 text-center border-2 border-dashed border-gray-200 dark:border-gray-700">
                        <FiUploadCloud className="w-14 h-14 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-700 dark:text-white mb-1">No uploads yet</h3>
                        <p className="text-gray-400 dark:text-gray-500 text-sm mb-5 max-w-xs mx-auto">
                            Upload your first media file — it will be encrypted, watermarked and stored securely.
                        </p>
                        <button
                            onClick={() => setShowUploader(true)}
                            className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 shadow-md transition-all"
                        >
                            Upload Now
                        </button>
                    </div>
                )}
            </motion.div>
        </div>
    );
};

export default Dashboard;
