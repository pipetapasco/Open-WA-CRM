import { useState, useEffect } from 'react';
import { Plus, Settings, ExternalLink, Loader2, Trash2, Copy, Check, Link2, Sparkles } from 'lucide-react';
import { getAccounts, deleteAccount } from '../../services/whatsappService';
import { getAIConfigs } from '../../services/aiService';
import ConnectAccountModal from '../../components/modals/ConnectAccountModal';
import EditAccountModal from '../../components/modals/EditAccountModal';
import AIConfigModal from '../../components/modals/AIConfigModal';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function AccountCard({ account, aiConfig, onDelete, onEdit, onConfigureAI }) {
    const [deleting, setDeleting] = useState(false);
    const [copied, setCopied] = useState(false);
    const isActive = account.status === 'active';

    const webhookUrl = `${API_BASE_URL}/config/webhook/${account.phone_number_id}/`;

    const handleDelete = async () => {
        if (!confirm(`¿Estás seguro de eliminar la cuenta "${account.name}"?`)) return;

        setDeleting(true);
        try {
            await deleteAccount(account.id);
            onDelete?.(account.id);
        } catch (err) {
            alert('Error al eliminar la cuenta');
        } finally {
            setDeleting(false);
        }
    };

    const handleCopyWebhook = async () => {
        try {
            await navigator.clipboard.writeText(webhookUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
        }
    };

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
            {/* Card Header */}
            <div className="p-4 border-b border-gray-100">
                <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">{account.name}</h3>
                    <span
                        className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${isActive
                            ? 'bg-green-50 text-green-700'
                            : 'bg-red-50 text-red-700'
                            }`}
                    >
                        <span
                            className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500' : 'bg-red-500'
                                }`}
                        />
                        {isActive ? 'Conectado' : 'Desconectado'}
                    </span>
                </div>
            </div>

            {/* Card Body */}
            <div className="p-4 space-y-3">
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Phone ID</p>
                    <p className="text-sm text-gray-700 font-mono">{account.phone_number_id}</p>
                </div>
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Business Account</p>
                    <p className="text-sm text-gray-700 font-mono">{account.business_account_id}</p>
                </div>

                {/* Webhook URL */}
                <div className="pt-2 border-t border-gray-100">
                    <div className="flex items-center gap-1 mb-1.5">
                        <Link2 size={12} className="text-gray-400" />
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Webhook URL</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <code className="flex-1 text-xs bg-gray-100 text-gray-700 px-2 py-1.5 rounded font-mono truncate">
                            {webhookUrl}
                        </code>
                        <button
                            onClick={handleCopyWebhook}
                            className={`p-1.5 rounded-lg transition-colors ${copied
                                ? 'bg-green-100 text-green-600'
                                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                }`}
                            title="Copiar URL"
                        >
                            {copied ? <Check size={14} /> : <Copy size={14} />}
                        </button>
                    </div>
                </div>

                {/* Indicadores de tokens */}
                <div className="flex gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${account.has_access_token ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {account.has_access_token ? '✓ Token' : '✗ Sin Token'}
                    </span>
                </div>

                {/* AI Status */}
                {aiConfig && (
                    <div className="pt-3 border-t border-gray-100">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Sparkles size={14} className="text-purple-500" />
                                <span className="text-xs text-gray-700">
                                    IA configurada: <span className="font-medium">{aiConfig.provider === 'gemini' ? 'Gemini' : aiConfig.provider}</span>
                                </span>
                            </div>
                            <div className="flex items-center gap-1">
                                <span className={`w-2 h-2 rounded-full ${aiConfig.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
                                <span className="text-xs text-gray-500">{aiConfig.enabled ? 'Activa' : 'Pausada'}</span>
                            </div>
                        </div>
                        <button
                            onClick={() => onConfigureAI(account, aiConfig)}
                            className="mt-2 w-full text-xs text-purple-600 hover:text-purple-700 font-medium py-1.5 hover:bg-purple-50 rounded transition-colors"
                        >
                            Editar configuración
                        </button>
                    </div>
                )}
            </div>

            {/* Card Footer */}
            <div className="px-4 py-3 bg-gray-50 rounded-b-xl border-t border-gray-100 flex flex-wrap gap-2">
                {!aiConfig && (
                    <button
                        onClick={() => onConfigureAI(account)}
                        className="flex-1 min-w-[120px] flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 hover:border-purple-300 transition-colors"
                    >
                        <Sparkles size={16} />
                        <span className="whitespace-nowrap">Configurar IA</span>
                    </button>
                )}
                <button
                    onClick={() => onEdit?.(account)}
                    className="flex-1 min-w-[100px] flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-colors"
                >
                    <Settings size={16} />
                    <span className="whitespace-nowrap">Gestionar</span>
                </button>
                <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50 hover:border-red-300 transition-colors disabled:opacity-50"
                >
                    {deleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                </button>
            </div>
        </div>
    );
}

function LoadingSkeleton() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
                    <div className="flex justify-between items-center mb-4">
                        <div className="h-5 bg-gray-200 rounded w-32"></div>
                        <div className="h-5 bg-gray-200 rounded w-20"></div>
                    </div>
                    <div className="space-y-3">
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default function WhatsAppAccountsPage() {
    const [accounts, setAccounts] = useState([]);
    const [aiConfigs, setAiConfigs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isAIModalOpen, setIsAIModalOpen] = useState(false);
    const [selectedAccount, setSelectedAccount] = useState(null);
    const [selectedAIConfig, setSelectedAIConfig] = useState(null);

    const fetchAccounts = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getAccounts();
            setAccounts(data);
            await fetchAIConfigs();
        } catch (err) {
            setError('No se pudieron cargar las cuentas. Verifica que el backend esté corriendo.');
        } finally {
            setLoading(false);
        }
    };

    const fetchAIConfigs = async () => {
        try {
            const data = await getAIConfigs();
            setAiConfigs(data);
        } catch (err) {
        }
    };

    useEffect(() => {
        fetchAccounts();
    }, []);

    const handleAccountCreated = () => {
        fetchAccounts();
    };

    const handleAccountUpdated = () => {
        fetchAccounts();
    };

    const handleAccountDeleted = (deletedId) => {
        setAccounts((prev) => prev.filter((acc) => acc.id !== deletedId));
    };

    const handleEditAccount = (account) => {
        setSelectedAccount(account);
        setIsEditModalOpen(true);
    };

    const handleConfigureAI = (account, existingConfig = null) => {
        setSelectedAccount(account);
        setSelectedAIConfig(existingConfig);
        setIsAIModalOpen(true);
    };

    const handleAIConfigSuccess = () => {
        fetchAIConfigs();
    };

    const getAIConfigForAccount = (accountId) => {
        return aiConfigs.find(config => config.account === accountId);
    };

    return (
        <div className="p-6 lg:p-8">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Canales de WhatsApp</h1>
                    <p className="text-gray-500 mt-1">
                        Gestiona tus cuentas de WhatsApp Business conectadas.
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 hover:shadow-md transition-all duration-200"
                    >
                        <Plus size={18} />
                        Conectar Cuenta
                    </button>
                </div>
            </div>

            {/* Error State */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {error}
                </div>
            )}

            {/* Loading State */}
            {loading && <LoadingSkeleton />}

            {/* Accounts Grid */}
            {!loading && !error && accounts.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {accounts.map((account) => (
                        <AccountCard
                            key={account.id}
                            account={account}
                            aiConfig={getAIConfigForAccount(account.id)}
                            onDelete={handleAccountDeleted}
                            onEdit={handleEditAccount}
                            onConfigureAI={handleConfigureAI}
                        />
                    ))}
                </div>
            )}

            {/* Empty State */}
            {!loading && !error && accounts.length === 0 && (
                <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                    <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                        <ExternalLink size={24} className="text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                        No hay cuentas conectadas
                    </h3>
                    <p className="text-gray-500 mb-4">
                        Conecta tu primera cuenta de WhatsApp Business para comenzar.
                    </p>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        <Plus size={16} />
                        Conectar Cuenta
                    </button>
                </div>
            )}

            {/* Create Account Modal */}
            <ConnectAccountModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSuccess={handleAccountCreated}
            />

            {/* Edit Account Modal */}
            <EditAccountModal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedAccount(null);
                }}
                account={selectedAccount}
                onSuccess={handleAccountUpdated}
            />

            {/* AI Configuration Modal */}
            <AIConfigModal
                isOpen={isAIModalOpen}
                onClose={() => {
                    setIsAIModalOpen(false);
                    setSelectedAccount(null);
                    setSelectedAIConfig(null);
                }}
                account={selectedAccount}
                existingConfig={selectedAIConfig}
                onSuccess={handleAIConfigSuccess}
            />
        </div>
    );
}
