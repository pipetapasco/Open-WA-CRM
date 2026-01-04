import { useState, useEffect } from 'react';
import {
    Bot,
    Key,
    MessageSquareText,
    Loader2,
    AlertCircle,
    Save,
    Sparkles,
} from 'lucide-react';
import Modal from '../ui/Modal';
import { createAIConfig, updateAIConfig, getAIProviders } from '../../services/aiService';

export default function AIConfigModal({ isOpen, onClose, account, existingConfig, onSuccess }) {
    const [formData, setFormData] = useState({
        enabled: true,
        provider: 'gemini',
        api_key: '',
        system_prompt: '',
        max_history_messages: 10,
    });
    const [providers, setProviders] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingProviders, setLoadingProviders] = useState(false);
    const [error, setError] = useState(null);

    // Fetch providers
    useEffect(() => {
        if (isOpen) {
            fetchProviders();
        }
    }, [isOpen]);

    // Load existing config or reset form
    useEffect(() => {
        if (isOpen) {
            if (existingConfig) {
                setFormData({
                    enabled: existingConfig.enabled,
                    provider: existingConfig.provider,
                    api_key: '', // Never show existing key
                    system_prompt: existingConfig.system_prompt || '',
                    max_history_messages: existingConfig.max_history_messages || 10,
                });
            } else {
                setFormData({
                    enabled: true,
                    provider: 'gemini',
                    api_key: '',
                    system_prompt: '',
                    max_history_messages: 10,
                });
            }
            setError(null);
        }
    }, [existingConfig, isOpen]);

    const fetchProviders = async () => {
        setLoadingProviders(true);
        try {
            const data = await getAIProviders();
            setProviders(data);
        } catch (err) {
            console.error('Error fetching providers:', err);
            // Fallback
            setProviders([{ id: 'gemini', name: 'Google Gemini' }]);
        } finally {
            setLoadingProviders(false);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const dataToSend = {
                ...formData,
                account: account.id,
            };

            // If updating and api_key is empty, don't send it
            if (existingConfig && formData.api_key === '') {
                delete dataToSend.api_key;
            }

            if (existingConfig) {
                await updateAIConfig(existingConfig.id, dataToSend);
            } else {
                await createAIConfig(dataToSend);
            }

            onSuccess?.();
            onClose();
        } catch (err) {
            console.error('Error saving AI config:', err);
            setError(
                err.response?.data?.detail ||
                err.response?.data?.api_key?.[0] ||
                err.response?.data?.account?.[0] ||
                'Error al guardar la configuración. Verifica los datos e intenta nuevamente.'
            );
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setError(null);
            onClose();
        }
    };

    if (!account) return null;

    return (
        <Modal isOpen={isOpen} onClose={handleClose} title="Configurar Inteligencia Artificial" size="lg">
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Header with Gemini branding */}
                <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100">
                    <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm">
                        <Sparkles className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900">
                            {existingConfig ? 'Editar configuración' : 'Activar asistente inteligente'}
                        </h3>
                        <p className="text-sm text-gray-600">
                            Cuenta: <span className="font-medium">{account.name}</span>
                        </p>
                    </div>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
                        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                {/* Enable Toggle */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div>
                        <label className="text-sm font-medium text-gray-900">
                            Habilitar asistente de IA
                        </label>
                        <p className="text-xs text-gray-500 mt-0.5">
                            Responde automáticamente a los mensajes entrantes
                        </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            name="enabled"
                            checked={formData.enabled}
                            onChange={handleChange}
                            className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                </div>

                {/* Provider Selection */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                        <Bot size={16} />
                        Proveedor de IA
                    </label>
                    <select
                        name="provider"
                        value={formData.provider}
                        onChange={handleChange}
                        disabled={loadingProviders}
                        required
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    >
                        {loadingProviders ? (
                            <option>Cargando proveedores...</option>
                        ) : (
                            providers.map((provider) => (
                                <option key={provider.id} value={provider.id}>
                                    {provider.name}
                                </option>
                            ))
                        )}
                    </select>
                </div>

                {/* API Key */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                        <Key size={16} />
                        API Key {existingConfig && <span className="text-xs text-gray-400 font-normal">(dejar vacío para mantener actual)</span>}
                    </label>
                    <input
                        type="password"
                        name="api_key"
                        value={formData.api_key}
                        onChange={handleChange}
                        required={!existingConfig}
                        placeholder={existingConfig ? "••••••••••••••••" : "Ingresa tu API Key de Google AI Studio"}
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors font-mono text-sm"
                    />
                    <p className="mt-1.5 text-xs text-gray-500">
                        Obtén tu API Key en{' '}
                        <a
                            href="https://aistudio.google.com/app/apikey"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                        >
                            Google AI Studio
                        </a>
                    </p>
                </div>

                {/* System Prompt */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                        <MessageSquareText size={16} />
                        Prompt del Sistema
                    </label>
                    <textarea
                        name="system_prompt"
                        value={formData.system_prompt}
                        onChange={handleChange}
                        rows={5}
                        placeholder="Ej: Eres un asistente útil para una pizzería. Ayuda a los clientes con pedidos y consultas sobre el menú..."
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
                    />
                    <p className="mt-1.5 text-xs text-gray-500">
                        Define el comportamiento y personalidad del asistente
                    </p>
                </div>

                {/* Max History Messages */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Mensajes de contexto
                    </label>
                    <input
                        type="number"
                        name="max_history_messages"
                        value={formData.max_history_messages}
                        onChange={handleChange}
                        min="1"
                        max="50"
                        required
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    />
                    <p className="mt-1.5 text-xs text-gray-500">
                        Cantidad de mensajes previos a incluir como contexto (1-50)
                    </p>
                </div>

                {/* Footer / Actions */}
                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
                    <button
                        type="button"
                        onClick={handleClose}
                        disabled={loading}
                        className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={16} className="animate-spin" />
                                Guardando...
                            </>
                        ) : (
                            <>
                                <Save size={16} />
                                {existingConfig ? 'Guardar Cambios' : 'Activar IA'}
                            </>
                        )}
                    </button>
                </div>
            </form>
        </Modal>
    );
}
