// Central API config — reads from Vite env variable at build time.
// Set VITE_API_URL in Render frontend environment variables:
//   VITE_API_URL = https://your-backend.onrender.com/api

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export default API_BASE;

// ─── Utility helpers (kept for Dashboard.jsx compatibility) ─────────────────

import axios from 'axios';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
};

export const uploadMedia = (file, mediaType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', mediaType);
    return axios.post(`${API_BASE}/upload`, formData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' },
    });
};
