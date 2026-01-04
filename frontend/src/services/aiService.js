import api from '../api/axios';

const AI_CONFIG_ENDPOINT = '/ai-bot/config/';

/**
 * Obtiene todas las configuraciones de IA del usuario
 * @param {Object} params - Parámetros de filtro (account, enabled)
 * @returns {Promise<Array>} Lista de configuraciones
 */
export async function getAIConfigs(params = {}) {
    const response = await api.get(AI_CONFIG_ENDPOINT, { params });
    return response.data;
}

/**
 * Obtiene una configuración de IA específica
 * @param {string} id - UUID de la configuración
 * @returns {Promise<Object>} Datos de la configuración
 */
export async function getAIConfig(id) {
    const response = await api.get(`${AI_CONFIG_ENDPOINT}${id}/`);
    return response.data;
}

/**
 * Crea una nueva configuración de IA
 * @param {Object} data - Datos de la configuración
 * @returns {Promise<Object>} Configuración creada
 */
export async function createAIConfig(data) {
    const response = await api.post(AI_CONFIG_ENDPOINT, data);
    return response.data;
}

/**
 * Actualiza una configuración de IA existente
 * @param {string} id - UUID de la configuración
 * @param {Object} data - Datos a actualizar
 * @returns {Promise<Object>} Configuración actualizada
 */
export async function updateAIConfig(id, data) {
    const response = await api.patch(`${AI_CONFIG_ENDPOINT}${id}/`, data);
    return response.data;
}

/**
 * Elimina una configuración de IA
 * @param {string} id - UUID de la configuración
 * @returns {Promise<void>}
 */
export async function deleteAIConfig(id) {
    await api.delete(`${AI_CONFIG_ENDPOINT}${id}/`);
}

/**
 * Obtiene la lista de proveedores de IA disponibles
 * @returns {Promise<Array>} Lista de proveedores [{ id, name }]
 */
export async function getAIProviders() {
    const response = await api.get(`${AI_CONFIG_ENDPOINT}providers/`);
    return response.data;
}
