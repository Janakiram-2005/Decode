import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadMedia } from '../services/api';
import UploadCard from '../components/UploadCard';
import { FiUploadCloud, FiFile, FiLock } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

const Upload = () => {
    const [file, setFile] = useState(null);
    const [mediaType, setMediaType] = useState('image');
    const [preview, setPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState(null);

    const onDrop = useCallback((acceptedFiles) => {
        const selectedFile = acceptedFiles[0];
        if (!selectedFile) return;

        // Reset previous result
        setResult(null);

        // Basic validation
        if (mediaType === 'image' && !selectedFile.type.startsWith('image/')) {
            toast.error('Please select an image file');
            return;
        }
        if (mediaType === 'text' && selectedFile.type !== 'text/plain') {
            // Allow .txt extensions even if mime is elusive, but warn if clearly not text
            if (!selectedFile.name.endsWith('.txt')) {
                toast.error('Please select a text (.txt) file');
                return;
            }
        }

        setFile(selectedFile);

        // Generate preview
        if (mediaType === 'image') {
            const objectUrl = URL.createObjectURL(selectedFile);
            setPreview(objectUrl);
        } else {
            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target.result?.substring(0, 200) + '...');
            reader.readAsText(selectedFile);
        }
    }, [mediaType]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: mediaType === 'image' ? { 'image/*': [] } : { 'text/plain': ['.txt'] },
        maxFiles: 1,
    });

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        try {
            const response = await uploadMedia(file, mediaType);
            setResult(response.data);
            setFile(null); // Clear file after successful upload
            setPreview(null);
            toast.success('File uploaded and verified successfully!');
        } catch (error) {
            console.error(error);
            // specific error for duplicate
            if (error.response?.status === 409) {
                toast.error('Duplicate file! This exact file already exists in the system.');
            } else {
                toast.error(error.response?.data?.detail || 'Upload failed');
            }
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-6">Secure Upload</h1>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
                <div className="flex gap-4 mb-6">
                    <button
                        onClick={() => { setMediaType('image'); setFile(null); setPreview(null); setResult(null); }}
                        className={`flex-1 py-3 rounded-lg font-medium transition-colors ${mediaType === 'image'
                                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 ring-2 ring-indigo-500'
                                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                            }`}
                    >
                        Image Upload
                    </button>
                    <button
                        onClick={() => { setMediaType('text'); setFile(null); setPreview(null); setResult(null); }}
                        className={`flex-1 py-3 rounded-lg font-medium transition-colors ${mediaType === 'text'
                                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 ring-2 ring-indigo-500'
                                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                            }`}
                    >
                        Text Upload
                    </button>
                </div>

                {!result && (
                    <div
                        {...getRootProps()}
                        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${isDragActive
                                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                                : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400 dark:hover:border-indigo-500'
                            }`}
                    >
                        <input {...getInputProps()} />
                        <div className="flex flex-col items-center gap-4 text-gray-500 dark:text-gray-400">
                            {preview ? (
                                <div className="relative">
                                    {mediaType === 'image' ? (
                                        <img src={preview} alt="Preview" className="max-h-64 rounded-lg shadow-md" />
                                    ) : (
                                        <div className="text-left bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-700 max-w-md w-full font-mono text-sm overflow-hidden">
                                            {preview}
                                        </div>
                                    )}
                                    <div className="mt-2 text-sm font-medium text-indigo-600">Click or drop to change file</div>
                                </div>
                            ) : (
                                <>
                                    <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-full">
                                        <FiUploadCloud className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
                                            Drag & drop your {mediaType} file here
                                        </p>
                                        <p className="text-sm">or click to browse</p>
                                    </div>
                                    <p className="text-xs text-gray-400">
                                        Max size: 10MB. Formats: {mediaType === 'image' ? 'JPG, PNG' : 'TXT'}
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                )}

                <AnimatePresence>
                    {file && !result && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-6"
                        >
                            <button
                                onClick={handleUpload}
                                disabled={uploading}
                                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {uploading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                        Processing & Hashing...
                                    </>
                                ) : (
                                    <>
                                        <FiLock /> Secure Upload & Hash
                                    </>
                                )}
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <AnimatePresence>
                {result && <UploadCard data={result} />}
            </AnimatePresence>
        </div>
    );
};

export default Upload;
