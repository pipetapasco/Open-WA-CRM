import { useState } from 'react';
import {
    MessageSquare,
    Key,
    Shield,
    Building2,
    Phone,
    Tag,
    Loader2,
    CheckCircle,
    AlertCircle,
} from 'lucide-react';
import Modal from '../ui/Modal';
import { createAccount } from '../../services/whatsappService';

const initialFormData = {
    name: '',
    phone_number_id: '',
    business_account_id: '',
    access_token: '',
    webhook_verify_token: '',
    status: 'active',
};

export default function ConnectAccountModal({ isOpen, onClose, onSuccess }) {
    const [formData, setFormData] = useState(initialFormData);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await createAccount(formData);
            setFormData(initialFormData);
            onSuccess?.();
            onClose();
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                err.response?.data?.phone_number_id?.[0] ||
                'Error al crear la cuenta. Verifica los datos e intenta nuevamente.'
            );
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setFormData(initialFormData);
            setError(null);
            onClose();
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={handleClose} title="Conectar Cuenta de WhatsApp" size="lg">
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Error Message */}
                {error && (
                    <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
                        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                {/* Información General */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <Tag size={16} />
                        <span>Información General</span>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Nombre de la cuenta *
                        </label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            required
                            placeholder="Ej: Ventas Principal, Soporte"
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            Nombre interno para identificar esta cuenta
                        </p>
                    </div>
                </div>

                {/* Configuración de Meta */}
                <div className="space-y-4 pt-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <Building2 size={16} />
                        <span>Configuración de Meta</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">
                                Phone Number ID *
                            </label>
                            <div className="relative">
                                <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    name="phone_number_id"
                                    value={formData.phone_number_id}
                                    onChange={handleChange}
                                    required
                                    placeholder="123456789012345"
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">
                                Business Account ID *
                            </label>
                            <div className="relative">
                                <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    name="business_account_id"
                                    value={formData.business_account_id}
                                    onChange={handleChange}
                                    required
                                    placeholder="WABA_ID"
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tokens de Seguridad */}
                <div className="space-y-4 pt-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <Shield size={16} />
                        <span>Tokens de Seguridad</span>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Access Token *
                        </label>
                        <div className="relative">
                            <Key size={16} className="absolute left-3 top-3 text-gray-400" />
                            <textarea
                                name="access_token"
                                value={formData.access_token}
                                onChange={handleChange}
                                required
                                rows={3}
                                placeholder="EAABw..."
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none font-mono text-sm"
                            />
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                            Token permanente de acceso a la API de WhatsApp Business
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Webhook Verify Token *
                        </label>
                        <div className="relative">
                            <Shield size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                name="webhook_verify_token"
                                value={formData.webhook_verify_token}
                                onChange={handleChange}
                                required
                                placeholder="mi_token_secreto"
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                            />
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                            Token para verificar la autenticidad de los webhooks de Meta
                        </p>
                    </div>
                </div>

                {/* Estado */}
                <div className="space-y-4 pt-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <CheckCircle size={16} />
                        <span>Estado</span>
                    </div>

                    <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="status"
                                value="active"
                                checked={formData.status === 'active'}
                                onChange={handleChange}
                                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">Activo</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="status"
                                value="disconnected"
                                checked={formData.status === 'disconnected'}
                                onChange={handleChange}
                                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">Desconectado</span>
                        </label>
                    </div>
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
                                Conectando...
                            </>
                        ) : (
                            <>
                                <MessageSquare size={16} />
                                Conectar Cuenta
                            </>
                        )}
                    </button>
                </div>
            </form>
        </Modal>
    );
}
