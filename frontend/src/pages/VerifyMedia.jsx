import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiUploadCloud, FiShield, FiFileText, FiImage, FiLoader } from 'react-icons/fi';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE from '../services/api';
import LayeredVerificationCard from '../components/LayeredVerificationCard';

const VerifyMedia = () => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0); // 0=idle 1=watermark 2=hash 3=similarity 4=ml 5=risk
    const [result, setResult] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                setIsAdmin(payload.role === 'admin');
            } catch { }
        }
    }, []);

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
            setResult(null);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        if (e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
            setResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setLoading(true);
        setLoadingStep(1);
        setResult(null);
        const formData = new FormData();
        formData.append('file', file);

        // Animate step indicator during loading
        const stepTimer = setTimeout(() => setLoadingStep(2), 1200);
        const stepTimer2 = setTimeout(() => setLoadingStep(3), 2400);
        const stepTimer3 = setTimeout(() => setLoadingStep(4), 3600);
        const stepTimer4 = setTimeout(() => setLoadingStep(5), 4800);

        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(`${API_BASE}/verify`, formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });
            setResult(response.data);
            if (response.data.matched) {
                toast.success('Match Found: Analysis Complete.');
            } else {
                toast('No match found.', { icon: '⚠️' });
            }
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || 'Verification failed');
        } finally {
            clearTimeout(stepTimer);
            if (typeof stepTimer2 !== 'undefined') clearTimeout(stepTimer2);
            if (typeof stepTimer3 !== 'undefined') clearTimeout(stepTimer3);
            if (typeof stepTimer4 !== 'undefined') clearTimeout(stepTimer4);
            setLoading(false);
            setLoadingStep(0);
        }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
                    <FiShield className="text-indigo-600" />
                    Media Verification Lab
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                    Upload suspicious media to cross-reference against the traceable database using Watermark extraction and SHA-256 forensics.
                </p>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Upload Section */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 h-fit"
                >
                    <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 dark:text-gray-200">
                        <FiUploadCloud /> Upload Evidence
                    </h2>

                    <div
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                        className={`border-3 border-dashed rounded-xl h-64 flex flex-col items-center justify-center cursor-pointer transition-all
                            ${file
                                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                                : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                            }`}
                    >
                        <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileChange} />

                        {file ? (
                            <div className="text-center p-4">
                                {file.type.startsWith('image/') ? (
                                    <FiImage className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
                                ) : (
                                    <FiFileText className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
                                )}
                                <p className="font-medium text-gray-800 dark:text-gray-200 truncate max-w-xs">{file.name}</p>
                                <p className="text-sm text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                        ) : (
                            <div className="text-center p-4 text-gray-400">
                                <FiUploadCloud className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                <p className="font-medium text-lg">Drag & Drop or Click to Upload</p>
                                <p className="text-sm mt-2 opacity-75">Supports Images & Text (Max 10MB)</p>
                            </div>
                        )}
                    </div>

                    <div className="mt-6 flex justify-end">
                        <button
                            onClick={handleUpload}
                            disabled={!file || loading}
                            className={`w-full py-3 rounded-lg font-bold shadow-md transition-all flex items-center justify-center gap-2
                                ${!file || loading
                                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:text-gray-500'
                                    : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-lg active:scale-[0.98]'
                                }`}
                        >
                            {loading ? (
                                <>
                                    <FiLoader className="animate-spin h-5 w-5" />
                                    {loadingStep === 1 ? 'Step 1: Checking Watermark...' :
                                     loadingStep === 2 ? 'Step 2: Checking Hash...' :
                                     loadingStep === 3 ? 'Step 3: Checking Similarity...' :
                                     loadingStep === 4 ? 'Step 4: Running ML Tamper Scan...' :
                                                         'Step 5: Aggregating Risk Score...'}
                                </>
                            ) : (
                                <>
                                    <FiShield /> Verify Media
                                </>
                            )}
                        </button>
                    </div>
                </motion.div>

                {/* Result Section */}
                <div className="relative">
                    <AnimatePresence mode='wait'>
                        {result ? (
                            <LayeredVerificationCard key="result" result={result} isAdmin={isAdmin} />
                        ) : (
                            !loading && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="h-full border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-2xl flex flex-col items-center justify-center text-gray-300 p-12 min-h-[400px]"
                                >
                                    <FiShield className="w-24 h-24 mb-4 opacity-20" />
                                    <p className="text-center opacity-60">
                                        Verification results will appear here<br />
                                        (Layer 1: Watermark | Layer 2: Hash | Layer 3: Similarity | Layer 4: ML Tamper | Layer 5: Risk Score)
                                    </p>
                                </motion.div>
                            )
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default VerifyMedia;
