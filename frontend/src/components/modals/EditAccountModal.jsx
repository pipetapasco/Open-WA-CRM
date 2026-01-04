import { useState, useEffect } from 'react';
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
    Save,
} from 'lucide-react';
import Modal from '../ui/Modal';
import { updateAccount } from '../../services/whatsappService';

export default function EditAccountModal({ isOpen, onClose, account, onSuccess }) {
    const [formData, setFormData] = useState({
        name: '',
        phone_number_id: '',
        business_account_id: '',
        access_token: '',
        webhook_verify_token: '',
        status: 'active',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Cargar datos de la cuenta cuando se abre el modal
    useEffect(() => {
        if (account && isOpen) {
            setFormData({
                name: account.name || '',
                phone_number_id: account.phone_number_id || '',
                business_account_id: account.business_account_id || '',
                access_token: '', // No mostramos el token existente por seguridad
                webhook_verify_token: '', // No mostramos el token existente
                status: account.status || 'active',
            });
            setError(null);
        }
    }, [account, isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Solo enviar campos que tienen valor (para no sobrescribir tokens con vacío)
            const dataToSend = {};
            Object.entries(formData).forEach(([key, value]) => {
                if (value !== '') {
                    dataToSend[key] = value;
                }
            });

            await updateAccount(account.id, dataToSend);
            onSuccess?.();
            onClose();
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                err.response?.data?.phone_number_id?.[0] ||
                'Error al actualizar la cuenta. Verifica los datos e intenta nuevamente.'
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
        <Modal isOpen={isOpen} onClose={handleClose} title="Editar Cuenta de WhatsApp" size="lg">
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
                        <span className="text-xs text-gray-400 font-normal">(dejar vacío para mantener actual)</span>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Access Token
                        </label>
                        <div className="relative">
                            <Key size={16} className="absolute left-3 top-3 text-gray-400" />
                            <textarea
                                name="access_token"
                                value={formData.access_token}
                                onChange={handleChange}
                                rows={3}
                                placeholder="Dejar vacío para mantener el token actual..."
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none font-mono text-sm"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Webhook Verify Token
                        </label>
                        <div className="relative">
                            <Shield size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                name="webhook_verify_token"
                                value={formData.webhook_verify_token}
                                onChange={handleChange}
                                placeholder="Dejar vacío para mantener el token actual..."
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                            />
                        </div>
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
                                Guardando...
                            </>
                        ) : (
                            <>
                                <Save size={16} />
                                Guardar Cambios
                            </>
                        )}
                    </button>
                </div>
            </form>
        </Modal>
    );
}
