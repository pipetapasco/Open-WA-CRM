import { useState, useEffect } from 'react';
import { X, Loader2, Send, FileText, AlertCircle, RefreshCw, CheckCircle } from 'lucide-react';
import { getTemplates, sendTemplateMessage, syncTemplates, createConversation, bulkSendTemplate } from '../../services/whatsappService';

/**
 * Modal para enviar mensajes de plantilla de WhatsApp.
 * 
 * Props:
 * - isOpen: boolean - Controla la visibilidad del modal
 * - onClose: () => void - Callback al cerrar el modal
 * - accountId: string - UUID de la cuenta de WhatsApp
 * - conversationId: string - UUID de la conversación (si existe)
 * - contactPhone: string - Número de teléfono del contacto
 * - contactName: string - Nombre del contacto
 * - recipients: Array - Lista de contactos para envío masivo (opcional)
 * - onSuccess: (message) => void - Callback cuando se envía exitosamente
 */
export default function SendTemplateModal({
    isOpen,
    onClose,
    accountId,
    contactId,
    conversationId,
    contactPhone,
    contactName,
    recipients,
    onSuccess
}) {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [error, setError] = useState(null);
    const [syncMessage, setSyncMessage] = useState(null);

    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [variableValues, setVariableValues] = useState({});

    // Cargar plantillas al abrir el modal
    useEffect(() => {
        if (isOpen && accountId) {
            loadTemplates();
        } else if (isOpen && !accountId) {
            setLoading(false);
            setError('No se pudo identificar la cuenta de WhatsApp.');
        }
    }, [isOpen, accountId]);

    const loadTemplates = async () => {
        setLoading(true);
        setError(null);
        setSyncMessage(null);
        try {
            const data = await getTemplates(accountId);
            setTemplates(data);
            if (data.length === 0) {
                setError('No hay plantillas aprobadas. Haz clic en "Sincronizar" para obtenerlas desde Meta.');
            }
        } catch (err) {
            setError('Error al cargar las plantillas.');
        } finally {
            setLoading(false);
        }
    };

    // Sincronizar plantillas desde Meta
    const handleSync = async () => {
        if (!accountId) return;

        setSyncing(true);
        setError(null);
        setSyncMessage(null);

        try {
            const result = await syncTemplates(accountId);
            setSyncMessage(`✓ ${result.synced} nuevas, ${result.updated} actualizadas`);
            // Recargar las plantillas después de sincronizar
            await loadTemplates();
        } catch (err) {
            setError('Error al sincronizar plantillas desde Meta.');
        } finally {
            setSyncing(false);
        }
    };

    // Extraer variables {{1}}, {{2}} o {{nombre}} del body de la plantilla
    // Retorna array de objetos: { key: '1' o 'customer_name', label: 'Variable 1' o 'customer_name', example: 'John' }
    const extractVariables = (template) => {
        if (!template?.components) return [];

        const components = Array.isArray(template.components)
            ? template.components
            : [];

        const bodyComponent = components.find(c => c.type === 'BODY');
        if (!bodyComponent?.text) return [];

        const variables = [];

        // Buscar todas las variables en el texto: {{1}}, {{2}} o {{nombre}}
        const allMatches = bodyComponent.text.match(/\{\{([^}]+)\}\}/g);
        if (!allMatches) return [];

        // Obtener ejemplos de variables con nombre si existen
        const namedExamples = {};
        if (bodyComponent.example?.body_text_named_params) {
            bodyComponent.example.body_text_named_params.forEach(param => {
                namedExamples[param.param_name] = param.example;
            });
        }

        // Obtener ejemplos de variables numeradas si existen
        const numberedExamples = bodyComponent.example?.body_text?.[0] || [];

        allMatches.forEach(match => {
            const key = match.replace(/[{}]/g, '');
            if (!variables.find(v => v.key === key)) {
                const isNumbered = /^\d+$/.test(key);
                const example = isNumbered
                    ? numberedExamples[parseInt(key) - 1]
                    : namedExamples[key];

                variables.push({
                    key,
                    label: isNumbered ? `Variable ${key}` : key.replace(/_/g, ' '),
                    example: example || ''
                });
            }
        });

        // Ordenar: primero las numeradas (por número), luego las con nombre (alfabético)
        return variables.sort((a, b) => {
            const aNum = parseInt(a.key);
            const bNum = parseInt(b.key);
            if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
            if (!isNaN(aNum)) return -1;
            if (!isNaN(bNum)) return 1;
            return a.key.localeCompare(b.key);
        });
    };

    // Obtener el texto del body de la plantilla
    const getTemplateBody = (template) => {
        if (!template?.components) return '';
        const components = Array.isArray(template.components) ? template.components : [];
        const bodyComponent = components.find(c => c.type === 'BODY');
        return bodyComponent?.text || '';
    };

    // Previsualizar el body con variables reemplazadas
    const getPreviewText = () => {
        if (!selectedTemplate) return '';
        let text = getTemplateBody(selectedTemplate);

        // Reemplazar todas las variables con sus valores o placeholder
        Object.entries(variableValues).forEach(([key, value]) => {
            const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
            text = text.replace(regex, value || `[${key}]`);
        });

        // Reemplazar variables que aún no tienen valor
        const variables = extractVariables(selectedTemplate);
        variables.forEach(v => {
            if (!variableValues[v.key]) {
                const regex = new RegExp(`\\{\\{${v.key}\\}\\}`, 'g');
                text = text.replace(regex, `[${v.label}]`);
            }
        });

        return text;
    };

    const handleTemplateSelect = (template) => {
        setSelectedTemplate(template);
        setVariableValues({});
    };

    const handleVariableChange = (varNum, value) => {
        setVariableValues(prev => ({
            ...prev,
            [varNum]: value
        }));
    };

    const handleSend = async () => {
        if (!selectedTemplate) return;

        // Si no hay conversación y no es envío masivo, necesitamos info de contacto
        if (!recipients && !conversationId && (!contactId && !accountId)) {
            setError('Falta información del contacto para iniciar la conversación');
            return;
        }

        const variables = extractVariables(selectedTemplate);

        // Verificar que todas las variables estén llenas
        const missingVars = variables.filter(v => !variableValues[v.key]?.trim());
        if (missingVars.length > 0) {
            setError(`Por favor completa todas las variables: ${missingVars.map(v => v.label).join(', ')}`);
            return;
        }

        setSending(true);
        setError(null);

        try {
            // Construir componentes con parámetros
            const components = [];
            if (variables.length > 0) {
                components.push({
                    type: 'body',
                    parameters: variables.map(v => {
                        const isPositional = /^\d+$/.test(v.key);
                        const param = {
                            type: 'text',
                            text: variableValues[v.key]
                        };

                        if (!isPositional) {
                            param.parameter_name = v.key;
                        }

                        return param;
                    })
                });
            }

            const templateData = {
                template_name: selectedTemplate.name,
                template_language: selectedTemplate.language,
                components
            };

            let result;

            // Lógica para ENVÍO MASIVO
            if (recipients && recipients.length > 0) {
                result = await bulkSendTemplate(
                    recipients.map(r => r.id),
                    templateData
                );
            } else {
                // Lógica de ENVÍO INDIVIDUAL (Original)
                let targetConversationId = conversationId;

                // Si no existe ID de conversación, crearla primero
                if (!targetConversationId) {
                    try {
                        const newConv = await createConversation({
                            contact: contactId,
                            account: accountId
                        });
                        targetConversationId = newConv.id;
                    } catch (err) {
                        throw new Error('No se pudo crear la conversación. Verifica la conexión.');
                    }
                }

                result = await sendTemplateMessage(targetConversationId, templateData);
            }

            onSuccess?.(result);
            onClose();
        } catch (err) {
            const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Error al enviar la plantilla. Por favor intenta de nuevo.';
            setError(errorMessage);
        } finally {
            setSending(false);
        }
    };

    if (!isOpen) return null;

    const variables = selectedTemplate ? extractVariables(selectedTemplate) : [];
    const isBulk = recipients && recipients.length > 0;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">Enviar Plantilla</h3>
                        <p className="text-sm text-gray-500 mt-0.5">
                            {isBulk ? (
                                <span className="font-semibold text-blue-600">
                                    Enviando a {recipients.length} contactos
                                </span>
                            ) : (
                                `Para: ${contactName || contactPhone}`
                            )}
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Sync Button */}
                        <button
                            onClick={handleSync}
                            disabled={syncing || loading}
                            title="Sincronizar plantillas desde Meta"
                            className="p-2 hover:bg-blue-50 rounded-full transition-colors disabled:opacity-50 group"
                        >
                            <RefreshCw
                                size={20}
                                className={`text-blue-500 group-hover:text-blue-600 ${syncing ? 'animate-spin' : ''}`}
                            />
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                        >
                            <X size={20} className="text-gray-500" />
                        </button>
                    </div>
                </div>

                {/* Sync Status Message */}
                {syncMessage && (
                    <div className="mx-6 mt-4 px-4 py-2.5 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700 text-sm">
                        <CheckCircle size={16} />
                        {syncMessage}
                    </div>
                )}

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 size={32} className="animate-spin text-blue-500" />
                        </div>
                    ) : error && templates.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                            <AlertCircle size={48} className="mb-4 text-yellow-500" />
                            <p className="text-center">{error}</p>
                        </div>
                    ) : (
                        <>
                            {/* Template Selector */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Selecciona una plantilla
                                </label>
                                <select
                                    value={selectedTemplate?.id || ''}
                                    onChange={(e) => {
                                        const template = templates.find(t => t.id === e.target.value);
                                        handleTemplateSelect(template);
                                    }}
                                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                                >
                                    <option value="">-- Seleccionar --</option>
                                    {templates.map(template => (
                                        <option key={template.id} value={template.id}>
                                            {template.name} ({template.language}) - {template.category}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Template Preview */}
                            {selectedTemplate && (
                                <>
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <FileText size={16} className="text-gray-500" />
                                            <span className="text-sm font-medium text-gray-700">Vista previa</span>
                                        </div>
                                        <p className="text-sm text-gray-800 whitespace-pre-wrap">
                                            {getPreviewText()}
                                        </p>
                                    </div>

                                    {/* Variable Inputs */}
                                    {variables.length > 0 && (
                                        <div className="space-y-3">
                                            <label className="block text-sm font-medium text-gray-700">
                                                Variables {isBulk && <span className="text-gray-400 font-normal">(se aplicarán a todos los contactos)</span>}
                                            </label>
                                            {variables.map(v => (
                                                <div key={v.key}>
                                                    <label className="block text-xs text-gray-500 mb-1">
                                                        {v.label}
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={variableValues[v.key] || ''}
                                                        onChange={(e) => handleVariableChange(v.key, e.target.value)}
                                                        placeholder={v.example ? `Ej: ${v.example}` : `Valor para {{${v.key}}}`}
                                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-sm"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}

                            {/* Error message */}
                            {error && templates.length > 0 && (
                                <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg flex items-center gap-2">
                                    <AlertCircle size={16} />
                                    {error}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="flex gap-3 px-6 py-4 bg-gray-50 border-t border-gray-100">
                    <button
                        onClick={onClose}
                        disabled={sending}
                        className="flex-1 px-4 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSend}
                        disabled={sending || !selectedTemplate || (!conversationId && (!contactId || !accountId) && !isBulk)}
                        className="flex-1 px-4 py-2.5 text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                    >
                        {sending ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                Enviando...
                            </>
                        ) : (
                            <>
                                <Send size={18} />
                                Enviar Plantilla
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
