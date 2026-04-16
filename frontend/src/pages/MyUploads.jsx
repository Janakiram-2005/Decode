import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiShield, FiFileText, FiDownload,
    FiTrash2, FiImage, FiCheckCircle, FiUploadCloud
} from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE from '../services/api';


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

// ─── MyUploads ───────────────────────────────────────────────────────────────
const MyUploads = () => {
    const navigate = useNavigate();
    const [uploads, setUploads] = useState([]);
    const [loading, setLoading] = useState(true);

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
            toast.error('Failed to load uploads');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchUploads(); }, []);

    const handleDelete = (mediaId) => {
        setUploads(prev => prev.filter(u => u.media_id !== mediaId));
    };

    return (
        <div className="p-6 md:p-8 max-w-screen-xl mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                {/* Header */}
                <div className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">My Uploads</h1>
                        <p className="text-gray-500 dark:text-gray-400 text-sm">View and manage the files you have securely uploaded.</p>
                    </div>
                    
                    {!loading && uploads.length > 0 && (
                         <div className="text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 font-semibold px-4 py-2 rounded-xl border border-indigo-100 dark:border-indigo-800">
                             Total: {uploads.length} files
                         </div>
                    )}
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
                        <p className="text-gray-400 dark:text-gray-500 text-sm max-w-xs mx-auto">
                            Head over to the secure upload page to add your first file.
                        </p>
                    </div>
                )}
            </motion.div>
        </div>
    );
};

export default MyUploads;
