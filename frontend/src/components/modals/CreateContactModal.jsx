import { useState, useEffect } from 'react';
import { User, Phone, Building2, Loader2, AlertCircle, UserPlus } from 'lucide-react';
import Modal from '../ui/Modal';
import { createContact, getAccounts } from '../../services/whatsappService';

const initialFormData = {
    name: '',
    phone_number: '',
    account: '',
};

export default function CreateContactModal({ isOpen, onClose, onSuccess }) {
    const [formData, setFormData] = useState(initialFormData);
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingAccounts, setLoadingAccounts] = useState(true);
    const [error, setError] = useState(null);

    // Cargar cuentas al abrir el modal
    useEffect(() => {
        if (isOpen) {
            setLoadingAccounts(true);
            getAccounts()
                .then((data) => {
                    setAccounts(data);
                    // Seleccionar la primera cuenta por defecto si hay
                    if (data.length > 0 && !formData.account) {
                        setFormData(prev => ({ ...prev, account: data[0].id }));
                    }
                })
                .catch((err) => {
                    console.error('Error loading accounts:', err);
                })
                .finally(() => {
                    setLoadingAccounts(false);
                });
        }
    }, [isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await createContact(formData);
            setFormData(initialFormData);
            onSuccess?.();
            onClose();
        } catch (err) {
            console.error('Error creating contact:', err);
            setError(
                err.response?.data?.detail ||
                err.response?.data?.phone_number?.[0] ||
                err.response?.data?.account?.[0] ||
                'Error al crear el contacto. Verifica los datos e intenta nuevamente.'
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
        <Modal isOpen={isOpen} onClose={handleClose} title="Nuevo Contacto" size="md">
            <form onSubmit={handleSubmit} className="space-y-5">
                {/* Error Message */}
                {error && (
                    <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
                        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                {/* Nombre */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Nombre del contacto *
                    </label>
                    <div className="relative">
                        <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            required
                            placeholder="Ej: Juan Pérez"
                            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        />
                    </div>
                </div>

                {/* Teléfono */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Número de WhatsApp *
                    </label>
                    <div className="relative">
                        <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            name="phone_number"
                            value={formData.phone_number}
                            onChange={handleChange}
                            required
                            placeholder="Ej: 573001234567"
                            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        />
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                        Incluye el código de país sin el signo +
                    </p>
                </div>

                {/* Cuenta de WhatsApp */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Cuenta de WhatsApp *
                    </label>
                    <div className="relative">
                        <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <select
                            name="account"
                            value={formData.account}
                            onChange={handleChange}
                            required
                            disabled={loadingAccounts}
                            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors appearance-none bg-white disabled:bg-gray-100"
                        >
                            {loadingAccounts ? (
                                <option value="">Cargando cuentas...</option>
                            ) : accounts.length === 0 ? (
                                <option value="">No hay cuentas disponibles</option>
                            ) : (
                                <>
                                    <option value="">Selecciona una cuenta</option>
                                    {accounts.map((acc) => (
                                        <option key={acc.id} value={acc.id}>
                                            {acc.name} ({acc.phone_number_id})
                                        </option>
                                    ))}
                                </>
                            )}
                        </select>
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
                        disabled={loading || accounts.length === 0}
                        className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={16} className="animate-spin" />
                                Creando...
                            </>
                        ) : (
                            <>
                                <UserPlus size={16} />
                                Crear Contacto
                            </>
                        )}
                    </button>
                </div>
            </form>
        </Modal>
    );
}
