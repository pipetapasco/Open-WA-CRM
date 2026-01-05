import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - Agregar Bearer token a cada petición
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - Manejar 401 y refresh token
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Si no hay respuesta (servidor caído), no intentar refresh
        if (!error.response) {
            return Promise.reject(error);
        }

        // Si es error 401 y no es un retry, y no es una ruta de auth
        const isAuthRoute = originalRequest.url?.includes('/auth/');
        if (error.response?.status === 401 && !originalRequest._retry && !isAuthRoute) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refreshToken');

                if (!refreshToken) {
                    // No hay refresh token, limpiar y dejar que el componente maneje
                    localStorage.removeItem('accessToken');
                    localStorage.removeItem('refreshToken');
                    return Promise.reject(error);
                }

                // Intentar refrescar el token usando axios directamente (no api)
                const response = await axios.post(
                    `${api.defaults.baseURL}/auth/refresh/`,
                    { refresh: refreshToken }
                );

                const { access } = response.data;
                localStorage.setItem('accessToken', access);

                // Reintentar la petición original con el nuevo token
                originalRequest.headers.Authorization = `Bearer ${access}`;
                return api(originalRequest);

            } catch (refreshError) {
                // Error al refrescar, limpiar tokens
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
