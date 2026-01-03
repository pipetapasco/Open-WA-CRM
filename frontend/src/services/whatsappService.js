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
 * Sincroniza plantillas de una cuenta (placeholder)
 * @param {string} id - UUID de la cuenta
 * @returns {Promise<Object>} Resultado de sincronización
 */
export async function syncTemplates(id) {
    const response = await api.get(`${ACCOUNTS_ENDPOINT}${id}/sync_templates/`);
    return response.data;
}
