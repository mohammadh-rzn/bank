import axios from 'axios';
import {message} from "antd";

const BASE_URL = process.env.REACT_APP_API_BASE_URL;
const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('access-token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        console.log('Request:', config);

        return config;
    },
    (error) => {
        console.error('Request Error:', error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        console.log('Response:', response);
        return response.data;
    },
    async (error) => {
        console.error('Response Error:', error);

        if (error.response && error.response.status === 403) {
            message.error("you have no access")
            window.location.href = '/login';
        }

        if (error.response && error.response.status === 401) {
            try {
                const refreshToken = sessionStorage.getItem("Refresher"); // Make sure the key matches exactly
                if (!refreshToken) {
                    message.error("No refresh token found");
                    window.location.href = '/login';
                }
                const refreshResponse = await axios.post(
                    BASE_URL + '/api/token/refresh/', {
                        refresh: refreshToken
                    }
                );
                sessionStorage.setItem("access-token", refreshResponse?.data?.access);
                error.config.headers['Authorization'] = `Bearer ${refreshResponse?.data?.access}`;
                return axios(error.config);
            } catch (refreshError) {
                console.error('Token refresh failed', refreshError);
                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

export default api;