import { useState, useEffect, useCallback } from 'react';
import { Search, User, MessageSquare, Phone, Building2, Loader2, Users, Plus, Send } from 'lucide-react';
import { getContacts } from '../../services/whatsappService';
import CreateContactModal from '../../components/modals/CreateContactModal';
import SendTemplateModal from '../../components/modals/SendTemplateModal';

function ContactRow({ contact, onNewMessage }) {
    return (
        <tr className="hover:bg-gray-50 transition-colors">
            {/* Avatar y Nombre */}
            <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-medium">
                        {contact.profile_picture_url ? (
                            <img
                                src={contact.profile_picture_url}
                                alt={contact.name}
                                className="w-10 h-10 rounded-full object-cover"
                            />
                        ) : (
                            <span>{contact.name?.charAt(0)?.toUpperCase() || '?'}</span>
                        )}
                    </div>
                    <div>
                        <p className="font-medium text-gray-900">{contact.name || 'Sin nombre'}</p>
                        <p className="text-sm text-gray-500 flex items-center gap-1">
                            <Phone size={12} />
                            {contact.phone_number}
                        </p>
                    </div>
                </div>
            </td>

            {/* Cuenta de WhatsApp */}
            <td className="px-6 py-4 whitespace-nowrap">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                    <Building2 size={12} />
                    {contact.account_name || 'Cuenta'}
                </span>
            </td>

            {/* Conversaciones */}
            <td className="px-6 py-4 whitespace-nowrap">
                <span className="inline-flex items-center gap-1.5 text-sm text-gray-600">
                    <MessageSquare size={14} className="text-blue-500" />
                    {contact.conversations_count || 0} chats
                </span>
            </td>

            {/* Fecha de creación */}
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {new Date(contact.created_at).toLocaleDateString('es-ES', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric'
                })}
            </td>

            {/* Acciones */}
            <td className="px-6 py-4 whitespace-nowrap text-right">
                <button
                    onClick={() => onNewMessage(contact)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-green-700 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                >
                    <Send size={14} />
                    Nuevo Mensaje
                </button>
            </td>
        </tr>
    );
}

function LoadingSkeleton() {
    return (
        <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-4 p-4 bg-white rounded-lg animate-pulse">
                    <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                    </div>
                    <div className="h-6 bg-gray-200 rounded w-20"></div>
                </div>
            ))}
        </div>
    );
}

export default function ContactsPage() {
    const [contacts, setContacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Estado para el modal de plantilla
    const [templateModalOpen, setTemplateModalOpen] = useState(false);
    const [selectedContact, setSelectedContact] = useState(null);

    const fetchContacts = useCallback(async (search = '') => {
        try {
            setLoading(true);
            setError(null);
            const params = search ? { search } : {};
            const data = await getContacts(params);
            setContacts(data);
        } catch (err) {
            console.error('Error fetching contacts:', err);
            setError('No se pudieron cargar los contactos.');
        } finally {
            setLoading(false);
        }
    }, []);

    // Cargar contactos al inicio y cuando cambia el término de búsqueda (con debounce)
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchContacts(searchTerm);
        }, searchTerm ? 400 : 0); // Sin delay para carga inicial

        return () => clearTimeout(timer);
    }, [searchTerm, fetchContacts]);

    const handleSearchChange = (e) => {
        setSearchTerm(e.target.value);
    };

    const handleContactCreated = () => {
        fetchContacts(searchTerm);
    };

    // Handler para abrir modal de nuevo mensaje
    const handleNewMessage = (contact) => {
        setSelectedContact(contact);
        setTemplateModalOpen(true);
    };

    return (
        <div className="p-6 lg:p-8">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Contactos</h1>
                    <p className="text-gray-500 mt-1">
                        {contacts.length} contacto{contacts.length !== 1 ? 's' : ''} en total
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    {/* Search Bar */}
                    <div className="relative w-full sm:w-64">
                        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={handleSearchChange}
                            placeholder="Buscar contacto..."
                            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        />
                    </div>

                    {/* Add Contact Button */}
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 hover:shadow-md transition-all duration-200"
                    >
                        <Plus size={18} />
                        Nuevo Contacto
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

            {/* Contacts Table */}
            {!loading && !error && contacts.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Contacto
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Cuenta
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Chats
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Añadido
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Acciones
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {contacts.map((contact) => (
                                <ContactRow
                                    key={contact.id}
                                    contact={contact}
                                    onNewMessage={handleNewMessage}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Empty State */}
            {!loading && !error && contacts.length === 0 && (
                <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                    <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                        <Users size={24} className="text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                        {searchTerm ? 'No se encontraron contactos' : 'Sin contactos'}
                    </h3>
                    <p className="text-gray-500 mb-4">
                        {searchTerm
                            ? `No hay resultados para "${searchTerm}"`
                            : 'Crea tu primer contacto o espera a recibir mensajes.'
                        }
                    </p>
                    {!searchTerm && (
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            <Plus size={16} />
                            Nuevo Contacto
                        </button>
                    )}
                </div>
            )}

            {/* Create Contact Modal */}
            <CreateContactModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSuccess={handleContactCreated}
            />

            {/* Send Template Modal */}
            {/* Nota: Para enviar plantillas desde Contactos, el contacto debe tener una conversación existente */}
            {selectedContact && (
                <SendTemplateModal
                    isOpen={templateModalOpen}
                    onClose={() => {
                        setTemplateModalOpen(false);
                        setSelectedContact(null);
                    }}
                    accountId={selectedContact.account}
                    contactId={selectedContact.id}
                    conversationId={selectedContact.conversations?.[0]?.id || null}
                    contactPhone={selectedContact.phone_number}
                    contactName={selectedContact.name}
                    onSuccess={() => {
                        setTemplateModalOpen(false);
                        setSelectedContact(null);
                        // Redirigir a inbox sería ideal aquí
                    }}
                />
            )}
        </div>
    );
}
