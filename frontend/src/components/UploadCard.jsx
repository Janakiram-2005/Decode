import { FiCheckCircle, FiCopy, FiFileText, FiImage } from 'react-icons/fi';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const UploadCard = ({ data }) => {
    if (!data) return null;

    const copyToClipboard = () => {
        navigator.clipboard.writeText(data.sha256_hash);
        toast.success('Hash copied to clipboard!');
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 p-6 max-w-2xl mx-auto mt-8"
        >
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100 dark:border-gray-700">
                <div className="bg-green-100 dark:bg-green-900/30 p-2 rounded-full">
                    <FiCheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Upload Successful</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Your file has been secured and hashed.</p>
                </div>
            </div>

            <div className="grid gap-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">File Type</span>
                        <div className="flex items-center gap-2 mt-1 text-gray-700 dark:text-gray-200">
                            {data.media_type === 'image' ? <FiImage /> : <FiFileText />}
                            <span className="capitalize">{data.media_type}</span>
                        </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">File Size</span>
                        <div className="mt-1 text-gray-700 dark:text-gray-200 font-mono">
                            {(data.file_size / 1024 / 1024).toFixed(2)} MB
                        </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Uploaded At</span>
                        <div className="mt-1 text-gray-700 dark:text-gray-200 text-sm">
                            {new Date(data.uploaded_at).toLocaleString()}
                        </div>
                    </div>
                </div>

                <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-lg border border-indigo-100 dark:border-indigo-800">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-semibold text-indigo-500 uppercase tracking-wider">SHA-256 Hash</span>
                        <button
                            onClick={copyToClipboard}
                            className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm flex items-center gap-1 transition-colors"
                        >
                            <FiCopy className="w-4 h-4" /> Copy
                        </button>
                    </div>
                    <code className="block break-all text-sm font-mono text-indigo-900 dark:text-indigo-100 bg-white dark:bg-gray-900 p-3 rounded border border-indigo-100 dark:border-indigo-800 select-all">
                        {data.sha256_hash}
                    </code>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Media ID</span>
                    <code className="text-xs font-mono text-gray-600 dark:text-gray-400 select-all">{data.media_id}</code>
                </div>
            </div>
        </motion.div>
    );
};

export default UploadCard;
