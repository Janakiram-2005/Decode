// Central API config — reads from Vite env variable at build time.
// Set VITE_API_URL in Render's Environment tab for the frontend service:
//   VITE_API_URL = https://your-backend.onrender.com/api

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export default API_BASE;

// ─── Axios instance ──────────────────────────────────────────────────────────

import axios from 'axios';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
};

// ─── Auth ────────────────────────────────────────────────────────────────────

export const loginUser = (email, password) => {
    const formData = new FormData();
    formData.append('username', email); // OAuth2PasswordRequestForm expects 'username'
    formData.append('password', password);
    return axios.post(`${API_BASE}/login`, formData);
};

export const registerUser = (email, password, adminSecret = '') => {
    return axios.post(`${API_BASE}/register`, {
        email,
        password,
        ...(adminSecret ? { admin_secret: adminSecret } : {}),
    });
};

// ─── Media ───────────────────────────────────────────────────────────────────

export const uploadMedia = (file, mediaType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', mediaType);
    return axios.post(`${API_BASE}/upload`, formData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' },
    });
};
