import api from '../api/axios';

const ACCOUNTS_ENDPOINT = '/config/accounts/';

/**
 * Obtiene todas las cuentas de WhatsApp
 * @returns {Promise<Array>} Lista de cuentas
 */
export async function getAccounts() {
    const response = await api.get(ACCOUNTS_ENDPOINT);
    return response.data;
}

/**
 * Crea una nueva cuenta de WhatsApp
 * @param {Object} data - Datos de la cuenta
 * @returns {Promise<Object>} Cuenta creada
 */
export async function createAccount(data) {
    const response = await api.post(ACCOUNTS_ENDPOINT, data);
    return response.data;
}

/**
 * Obtiene una cuenta específica
 * @param {string} id - UUID de la cuenta
 * @returns {Promise<Object>} Datos de la cuenta
 */
export async function getAccount(id) {
    const response = await api.get(`${ACCOUNTS_ENDPOINT}${id}/`);
    return response.data;
}

/**
 * Actualiza una cuenta existente
 * @param {string} id - UUID de la cuenta
 * @param {Object} data - Datos a actualizar
 * @returns {Promise<Object>} Cuenta actualizada
 */
export async function updateAccount(id, data) {
    const response = await api.patch(`${ACCOUNTS_ENDPOINT}${id}/`, data);
    return response.data;
}

/**
 * Elimina una cuenta
 * @param {string} id - UUID de la cuenta
 * @returns {Promise<void>}
 */
export async function deleteAccount(id) {
    await api.delete(`${ACCOUNTS_ENDPOINT}${id}/`);
}

/**
 * Sincroniza plantillas de una cuenta desde Meta API
 * @param {string} id - UUID de la cuenta
 * @returns {Promise<Object>} Resultado de sincronización
 */
export async function syncTemplates(id) {
    const response = await api.post(`${ACCOUNTS_ENDPOINT}${id}/sync_templates/`);
    return response.data;
}

// ============== CONTACTS ==============

const CONTACTS_ENDPOINT = '/contacts/contacts/';

/**
 * Obtiene todos los contactos con filtros opcionales
 * @param {Object} params - Parámetros de filtro (search, account)
 * @returns {Promise<Array>} Lista de contactos
 */
export async function getContacts(params = {}) {
    const response = await api.get(CONTACTS_ENDPOINT, { params });
    return response.data;
}

/**
 * Obtiene un contacto específico
 * @param {string} id - UUID del contacto
 * @returns {Promise<Object>} Datos del contacto
 */
export async function getContact(id) {
    const response = await api.get(`${CONTACTS_ENDPOINT}${id}/`);
    return response.data;
}

/**
 * Crea un nuevo contacto
 * @param {Object} data - Datos del contacto
 * @returns {Promise<Object>} Contacto creado
 */
export async function createContact(data) {
    const response = await api.post(CONTACTS_ENDPOINT, data);
    return response.data;
}

/**
 * Elimina un contacto
 * @param {string} id - UUID del contacto
 * @returns {Promise<void>}
 */
export async function deleteContact(id) {
    await api.delete(`${CONTACTS_ENDPOINT}${id}/`);
}

/**
 * Actualiza un contacto
 * @param {string} id - UUID del contacto
 * @param {Object} data - Datos a actualizar (name, etc.)
 * @returns {Promise<Object>} Contacto actualizado
 */
export async function updateContact(id, data) {
    const response = await api.patch(`${CONTACTS_ENDPOINT}${id}/`, data);
    return response.data;
}

/**
 * Elimina múltiples contactos
 * @param {Array<string>} ids - Lista de UUIDs de contactos
 * @returns {Promise<Object>} Resultado
 */
export async function bulkDeleteContacts(ids) {
    const response = await api.post(`${CONTACTS_ENDPOINT}bulk_delete/`, { ids });
    return response.data;
}

/**
 * Envía plantilla a múltiples contactos
 * @param {Array<string>} ids - Lista de UUIDs de contactos
 * @param {Object} templateData - Datos de la plantilla
 * @returns {Promise<Object>} Resultado
 */
export async function bulkSendTemplate(ids, templateData) {
    const response = await api.post(`${CONTACTS_ENDPOINT}bulk_send_template/`, {
        ids,
        template_data: templateData
    });
    return response.data;
}

// ============== CHAT ==============

const CONVERSATIONS_ENDPOINT = '/chat/conversations/';
const MESSAGES_ENDPOINT = '/chat/messages/';

/**
 * Obtiene todas las conversaciones
 * @param {Object} params - Parámetros de filtro (status, account)
 * @returns {Promise<Array>} Lista de conversaciones
 */
export async function getConversations(params = {}) {
    const response = await api.get(CONVERSATIONS_ENDPOINT, { params });
    return response.data;
}

/**
 * Crea una nueva conversación
 * @param {Object} data - Datos { contact: uuid, account: uuid }
 * @returns {Promise<Object>} Conversación creada
 */
export async function createConversation(data) {
    const response = await api.post(CONVERSATIONS_ENDPOINT, data);
    return response.data;
}

/**
 * Obtiene una conversación específica
 * @param {string} id - UUID de la conversación
 * @returns {Promise<Object>} Datos de la conversación
 */
export async function getConversation(id) {
    const response = await api.get(`${CONVERSATIONS_ENDPOINT}${id}/`);
    return response.data;
}

/**
 * Obtiene mensajes de una conversación (paginados)
 * @param {string} conversationId - UUID de la conversación
 * @param {number} page - Número de página
 * @returns {Promise<Object>} Respuesta paginada con mensajes
 */
export async function getMessages(conversationId, page = 1) {
    const response = await api.get(MESSAGES_ENDPOINT, {
        params: { conversation: conversationId, page }
    });
    return response.data;
}

/**
 * Envía un mensaje de texto a una conversación
 * @param {string} conversationId - UUID de la conversación
 * @param {string} text - Texto del mensaje
 * @returns {Promise<Object>} Mensaje creado
 */
export async function sendMessage(conversationId, text) {
    const response = await api.post(`${MESSAGES_ENDPOINT}${conversationId}/send_text/`, {
        message: text
    });
    return response.data;
}

/**
 * Marca todos los mensajes de una conversación como leídos
 * @param {string} conversationId - UUID de la conversación
 * @returns {Promise<Object>} Resultado
 */
export async function markAsRead(conversationId) {
    const response = await api.post(`${MESSAGES_ENDPOINT}${conversationId}/mark_as_read/`);
    return response.data;
}

/**
 * Actualiza el estado de una conversación
 * @param {string} id - UUID de la conversación
 * @param {Object} data - Datos a actualizar (status, etc.)
 * @returns {Promise<Object>} Conversación actualizada
 */
export async function updateConversation(id, data) {
    const response = await api.patch(`${CONVERSATIONS_ENDPOINT}${id}/`, data);
    return response.data;
}

/**
 * Elimina una conversación y todos sus archivos multimedia
 * @param {string} id - UUID de la conversación
 * @returns {Promise<Object>} Resultado de eliminación
 */
export async function deleteConversation(id) {
    const response = await api.delete(`${CONVERSATIONS_ENDPOINT}${id}/`);
    return response.data;
}

// ============== TEMPLATES ==============

const TEMPLATES_ENDPOINT = '/config/templates/';

/**
 * Obtiene plantillas aprobadas para una cuenta
 * @param {string} accountId - UUID de la cuenta
 * @returns {Promise<Array>} Lista de plantillas aprobadas
 */
export async function getTemplates(accountId) {
    const response = await api.get(TEMPLATES_ENDPOINT, {
        params: {
            account: accountId,
            status: 'APPROVED'
        }
    });
    return response.data;
}

/**
 * Envía un mensaje de plantilla a una conversación
 * @param {string} conversationId - UUID de la conversación
 * @param {Object} templateData - Datos de la plantilla
 * @param {string} templateData.template_name - Nombre de la plantilla
 * @param {string} templateData.template_language - Código de idioma
 * @param {Array} templateData.components - Componentes con variables
 * @returns {Promise<Object>} Mensaje creado
 */
export async function sendTemplateMessage(conversationId, templateData) {
    const response = await api.post(`${MESSAGES_ENDPOINT}${conversationId}/send_template/`, templateData);
    return response.data;
}
