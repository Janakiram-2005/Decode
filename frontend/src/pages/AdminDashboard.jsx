import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_BASE from '../services/api';
import { FiFileText, FiImage, FiHash, FiShield, FiUser, FiUploadCloud } from 'react-icons/fi';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const AdminDashboard = () => {
    const [mediaItems, setMediaItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }

        // Fetch Admin Media
        const fetchMedia = async () => {
            try {
                const response = await axios.get(`${API_BASE}/admin/media`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setMediaItems(response.data);
            } catch (error) {
                console.error("Failed to fetch media:", error);
                if (error.response && error.response.status === 403) {
                    toast.error("Access Denied: Admins Only");
                    navigate('/dashboard');
                } else {
                    toast.error("Failed to load admin data");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchMedia();
    }, [navigate]);

    const handleUploadWorkspaceDoc = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        let mediaType = '';
        if (file.type.startsWith('image/')) mediaType = 'image';
        else if (file.type === 'text/plain') mediaType = 'text';
        else {
            toast.error("Unsupported file type. Please upload Image or TXT.");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('media_type', mediaType);

        const uploadToast = toast.loading('Uploading to Workspace...');
        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API_BASE}/workspace/upload`, formData, {
                headers: { 
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });
            toast.success("Workspace document uploaded natively!", { id: uploadToast });
            // Optionally, refresh a list if we show workspace docs here
            // But we already have a dedicated page for them!
        } catch (error) {
            toast.error(error.response?.data?.detail || "Upload failed.", { id: uploadToast });
        }
        
        event.target.value = null; // reset input
    };

    if (loading) {
        return <div className="p-8 text-center text-gray-500 dark:text-gray-400">Loading Admin Dashboard...</div>;
    }

    return (
        <div className="p-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">Admin Dashboard</h1>
                        <p className="text-gray-500 dark:text-gray-400">Master view of all verified media assets.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <label className="cursor-pointer bg-green-100 hover:bg-green-200 text-green-700 px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors">
                            <FiUploadCloud /> Upload to Workspace
                            <input 
                                type="file" 
                                className="hidden" 
                                accept="image/png, image/jpeg, text/plain" 
                                onChange={handleUploadWorkspaceDoc} 
                            />
                        </label>
                        <div className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-lg font-semibold flex items-center gap-2">
                            <FiShield /> Admin Mode
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {mediaItems.map((item) => (
                        <div key={item.media_id} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden flex flex-col">
                            {/* Header */}
                            <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-start">
                                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                    {item.media_type === 'image' ? <FiImage className="text-blue-500" /> : <FiFileText className="text-orange-500" />}
                                    <span className="font-mono text-xs truncate max-w-[150px]">{item.media_id}</span>
                                </div>
                                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">Verified</span>
                            </div>

                            {/* Content Preview */}
                            <div className="h-48 bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4 overflow-hidden relative group">
                                {item.media_type === 'image' && item.url ? (
                                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="block w-full h-full">
                                        <img src={item.url} alt="Evidence" className="w-full h-full object-cover rounded-md transition-transform group-hover:scale-105" />
                                    </a>
                                ) : (
                                    <div className="text-gray-400 text-center text-sm p-4 overflow-y-auto max-h-full w-full">
                                        {item.media_type === 'text' ? (
                                            <p className="whitespace-pre-wrap text-left font-mono text-xs text-gray-600 dark:text-gray-300">
                                                Original Text Content (Stored securely)
                                            </p>
                                        ) : (
                                            <FiFileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Footer / Meta */}
                            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 flex-1 flex flex-col justify-end gap-2 text-xs">
                                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400" title="SHA256 Hash">
                                    <FiHash className="flex-shrink-0" />
                                    <span className="font-mono truncate">{item.sha256_hash}</span>
                                </div>
                                <div className="flex justify-between items-center text-gray-500 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                                    <span className="flex items-center gap-1">
                                        <FiUser /> {item.uploader_email || (item.user_id ? "User " + item.user_id.substring(0, 6) : "Unknown")}
                                    </span>
                                    <span>{new Date(item.uploaded_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        </div>
                    ))}

                    {mediaItems.length === 0 && (
                        <div className="col-span-full text-center py-12 text-gray-500">
                            No media uploads found in the system.
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};

export default AdminDashboard;
