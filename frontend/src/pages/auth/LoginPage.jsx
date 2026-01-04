import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Eye, EyeOff, LogIn, Loader2 } from 'lucide-react';

export default function LoginPage() {
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await login(formData.username, formData.password);
            navigate('/inbox');
        } catch (err) {
            const message = err.response?.data?.detail ||
                err.response?.data?.message ||
                'Credenciales inválidas. Inténtalo de nuevo.';
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="w-full max-w-md">
                {/* Logo y título */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">
                        Open<span className="text-blue-600">WA</span>
                    </h1>
                    <p className="text-gray-500 mt-2">Inicia sesión para continuar</p>
                </div>

                {/* Formulario */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        {/* Usuario */}
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                                Usuario
                            </label>
                            <input
                                type="text"
                                id="username"
                                name="username"
                                value={formData.username}
                                onChange={handleChange}
                                required
                                autoComplete="username"
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                                placeholder="Ingresa tu usuario"
                            />
                        </div>

                        {/* Contraseña */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                Contraseña
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                    autoComplete="current-password"
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none pr-12"
                                    placeholder="Ingresa tu contraseña"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>

                        {/* Botón submit */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    <span>Iniciando sesión...</span>
                                </>
                            ) : (
                                <>
                                    <LogIn size={20} />
                                    <span>Iniciar Sesión</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Link a registro */}
                    <div className="mt-6 text-center text-sm text-gray-600">
                        ¿No tienes una cuenta?{' '}
                        <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
                            Regístrate aquí
                        </Link>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center text-xs text-gray-400 mt-6">Open-WA CRM v1.0</p>
            </div>
        </div>
    );
}
