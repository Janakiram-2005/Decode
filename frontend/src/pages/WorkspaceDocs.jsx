import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../services/api';
import { FiDownload, FiFileText, FiImage, FiClock, FiUser } from 'react-icons/fi';
import toast from 'react-hot-toast';

const WorkspaceDocs = () => {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchDocs = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${API_BASE}/workspace/list`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setDocs(res.data);
        } catch (error) {
            toast.error("Failed to fetch workspace documents.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocs();
    }, []);

    const handleDownload = async (doc) => {
        const loadingToast = toast.loading("Applying personalized security watermark...");
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_BASE}/workspace/download/${doc.doc_id}`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            });

            // Handle file download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            
            // Extract filename from response headers or use doc's filename
            let fileName = `secure_${doc.filename}`;
            const contentDisposition = response.headers['content-disposition'];
            if (contentDisposition && contentDisposition.includes('filename=')) {
                fileName = contentDisposition.split('filename=')[1].replace(/["']/g, '');
            }
            
            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            toast.success("Document downloaded securely!", { id: loadingToast });
        } catch (error) {
            toast.error("Failed to download document.", { id: loadingToast });
            console.error(error);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading Workspace...</div>;

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Workspace Documents</h1>
                <p className="text-gray-500 mt-2">Shared documents. Downloads are dynamically secured with your user profile.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {docs.length === 0 ? (
                    <div className="col-span-full py-12 text-center text-gray-400 bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-600">
                        <FiFileText className="mx-auto w-12 h-12 mb-3 text-gray-300" />
                        <p>No documents exist in the workspace yet.</p>
                    </div>
                ) : (
                    docs.map(doc => (
                        <div key={doc.doc_id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden shadow-sm flex flex-col">
                            <div className="p-5 flex-1">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className={`p-3 rounded-xl ${doc.media_type === 'image' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'}`}>
                                        {doc.media_type === 'image' ? <FiImage size={24} /> : <FiFileText size={24} />}
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-800 dark:text-white truncate max-w-[200px]" title={doc.filename}>
                                            {doc.filename}
                                        </h3>
                                        <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                                            <FiClock /> {new Date(doc.uploaded_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 border-t border-gray-100 dark:border-gray-700 pt-4">
                                    <div className="flex items-center justify-between">
                                        <span className="flex items-center gap-1.5"><FiUser /> Uploaded by</span>
                                        <span className="truncate max-w-[120px]">{doc.uploaded_by}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span>Size</span>
                                        <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-100 dark:border-gray-700">
                                <button 
                                    onClick={() => handleDownload(doc)}
                                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                                >
                                    <FiDownload /> Secure Download
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default WorkspaceDocs;
