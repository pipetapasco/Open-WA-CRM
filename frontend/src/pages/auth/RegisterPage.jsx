import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Eye, EyeOff, UserPlus, Loader2 } from 'lucide-react';

export default function RegisterPage() {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        password_confirm: '',
        first_name: '',
        last_name: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.username) {
            newErrors.username = 'El usuario es requerido';
        }
        if (!formData.email) {
            newErrors.email = 'El correo es requerido';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'El correo no es válido';
        }
        if (!formData.password) {
            newErrors.password = 'La contraseña es requerida';
        } else if (formData.password.length < 8) {
            newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
        }
        if (formData.password !== formData.password_confirm) {
            newErrors.password_confirm = 'Las contraseñas no coinciden';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) return;

        setLoading(true);
        setErrors({});

        try {
            await register(formData);
            setSuccess(true);
            setTimeout(() => {
                navigate('/login');
            }, 2000);
        } catch (err) {
            const responseErrors = err.response?.data;
            if (responseErrors) {
                const formattedErrors = {};
                Object.keys(responseErrors).forEach(key => {
                    formattedErrors[key] = Array.isArray(responseErrors[key])
                        ? responseErrors[key][0]
                        : responseErrors[key];
                });
                setErrors(formattedErrors);
            } else {
                setErrors({ general: 'Error al registrar. Inténtalo de nuevo.' });
            }
        } finally {
            setLoading(false);
        }
    };

    const inputClasses = (fieldName) => `
    w-full px-4 py-3 border rounded-lg transition-all outline-none
    ${errors[fieldName]
            ? 'border-red-300 focus:ring-2 focus:ring-red-500 focus:border-transparent'
            : 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent'}
  `;

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8">
            <div className="w-full max-w-md">
                {/* Logo y título */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">
                        Open<span className="text-blue-600">WA</span>
                    </h1>
                    <p className="text-gray-500 mt-2">Crea tu cuenta para comenzar</p>
                </div>

                {/* Formulario */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
                    {success ? (
                        <div className="text-center py-8">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
                                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold text-gray-800 mb-2">¡Registro exitoso!</h3>
                            <p className="text-gray-600">Redirigiendo al inicio de sesión...</p>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-5">
                            {errors.general && (
                                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                                    {errors.general}
                                </div>
                            )}

                            {/* Nombre y Apellido */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre
                                    </label>
                                    <input
                                        type="text"
                                        id="first_name"
                                        name="first_name"
                                        value={formData.first_name}
                                        onChange={handleChange}
                                        className={inputClasses('first_name')}
                                        placeholder="Tu nombre"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
                                        Apellido
                                    </label>
                                    <input
                                        type="text"
                                        id="last_name"
                                        name="last_name"
                                        value={formData.last_name}
                                        onChange={handleChange}
                                        className={inputClasses('last_name')}
                                        placeholder="Tu apellido"
                                    />
                                </div>
                            </div>

                            {/* Usuario */}
                            <div>
                                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                                    Usuario *
                                </label>
                                <input
                                    type="text"
                                    id="username"
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    required
                                    className={inputClasses('username')}
                                    placeholder="Elige un nombre de usuario"
                                />
                                {errors.username && (
                                    <p className="mt-1 text-sm text-red-600">{errors.username}</p>
                                )}
                            </div>

                            {/* Email */}
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                    Correo electrónico *
                                </label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                    className={inputClasses('email')}
                                    placeholder="correo@ejemplo.com"
                                />
                                {errors.email && (
                                    <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                                )}
                            </div>

                            {/* Contraseña */}
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                    Contraseña *
                                </label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        id="password"
                                        name="password"
                                        value={formData.password}
                                        onChange={handleChange}
                                        required
                                        className={`${inputClasses('password')} pr-12`}
                                        placeholder="Mínimo 8 caracteres"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                                    >
                                        {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                    </button>
                                </div>
                                {errors.password && (
                                    <p className="mt-1 text-sm text-red-600">{errors.password}</p>
                                )}
                            </div>

                            {/* Confirmar Contraseña */}
                            <div>
                                <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700 mb-2">
                                    Confirmar Contraseña *
                                </label>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password_confirm"
                                    name="password_confirm"
                                    value={formData.password_confirm}
                                    onChange={handleChange}
                                    required
                                    className={inputClasses('password_confirm')}
                                    placeholder="Repite tu contraseña"
                                />
                                {errors.password_confirm && (
                                    <p className="mt-1 text-sm text-red-600">{errors.password_confirm}</p>
                                )}
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
                                        <span>Registrando...</span>
                                    </>
                                ) : (
                                    <>
                                        <UserPlus size={20} />
                                        <span>Crear Cuenta</span>
                                    </>
                                )}
                            </button>
                        </form>
                    )}

                    {/* Link a login */}
                    {!success && (
                        <div className="mt-6 text-center text-sm text-gray-600">
                            ¿Ya tienes una cuenta?{' '}
                            <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
                                Inicia sesión
                            </Link>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <p className="text-center text-xs text-gray-400 mt-6">Open-WA CRM v1.0</p>
            </div>
        </div>
    );
}
