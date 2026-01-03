import { useEffect, useRef, useCallback, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat/inbox/';

/**
 * Hook para gestionar la conexión WebSocket con el chat.
 * 
 * @param {Object} options
 * @param {Function} options.onNewMessage - Callback cuando llega un nuevo mensaje
 * @param {Function} options.onConversationUpdate - Callback para actualizaciones de conversación
 * @param {Function} options.onConnectionChange - Callback cuando cambia el estado de conexión
 */
export default function useChatWebSocket({
    onNewMessage,
    onConversationUpdate,
    onStatusUpdate,
    onConnectionChange
} = {}) {
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const [isConnected, setIsConnected] = useState(false);

    const connect = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const socket = new WebSocket(WS_URL);

            socket.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                onConnectionChange?.(true);
            };

            socket.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code);
                setIsConnected(false);
                onConnectionChange?.(false);

                if (!reconnectTimeoutRef.current) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectTimeoutRef.current = null;
                        connect();
                    }, 3000);
                }
            };

            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message:', data);

                    switch (data.type) {
                        case 'new_message':
                            onNewMessage?.(data.message);
                            break;
                        case 'conversation_update':
                            onConversationUpdate?.(data.conversation);
                            break;
                        case 'status_update':
                            onStatusUpdate?.(data.status_update);
                            break;
                        case 'connection_established':
                            console.log('WebSocket handshake complete');
                            break;
                        default:
                            console.log('Unknown message type:', data.type);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            socketRef.current = socket;
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }, [onNewMessage, onConversationUpdate, onStatusUpdate, onConnectionChange]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (socketRef.current) {
            socketRef.current.close();
            socketRef.current = null;
        }
    }, []);

    const sendMessage = useCallback((data) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }, []);

    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    return {
        isConnected,
        sendMessage,
        reconnect: connect,
    };
}
