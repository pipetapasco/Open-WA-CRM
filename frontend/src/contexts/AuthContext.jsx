import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const checkAuth = useCallback(async () => {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            const response = await api.get('/auth/me/');
            setUser(response.data);
        } catch (error) {
            // Token inválido o expirado - limpiar sin redireccionar
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const login = async (username, password) => {
        const response = await api.post('/auth/login/', { username, password });
        const { access, refresh } = response.data;

        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);

        // Obtener info del usuario
        const userResponse = await api.get('/auth/me/');
        setUser(userResponse.data);

        return response.data;
    };

    const register = async (userData) => {
        const response = await api.post('/auth/register/', userData);
        return response.data;
    };

    const logout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setUser(null);
    };

    const value = {
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        checkAuth,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthContext;
