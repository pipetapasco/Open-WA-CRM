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

    const onNewMessageRef = useRef(onNewMessage);
    const onConversationUpdateRef = useRef(onConversationUpdate);
    const onStatusUpdateRef = useRef(onStatusUpdate);
    const onConnectionChangeRef = useRef(onConnectionChange);

    useEffect(() => {
        onNewMessageRef.current = onNewMessage;
        onConversationUpdateRef.current = onConversationUpdate;
        onStatusUpdateRef.current = onStatusUpdate;
        onConnectionChangeRef.current = onConnectionChange;
    }, [onNewMessage, onConversationUpdate, onStatusUpdate, onConnectionChange]);

    const connect = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const socket = new WebSocket(WS_URL);

            socket.onopen = () => {
                setIsConnected(true);
                onConnectionChangeRef.current?.(true);
            };

            socket.onclose = (event) => {
                setIsConnected(false);
                onConnectionChangeRef.current?.(false);

                if (!reconnectTimeoutRef.current) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectTimeoutRef.current = null;
                        connect();
                    }, 3000);
                }
            };

            socket.onerror = () => {
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    switch (data.type) {
                        case 'new_message':
                            onNewMessageRef.current?.(data.message);
                            break;
                        case 'conversation_update':
                            onConversationUpdateRef.current?.(data.conversation);
                            break;
                        case 'status_update':
                            onStatusUpdateRef.current?.(data.status_update);
                            break;
                        case 'connection_established':
                            break;
                        default:
                    }
                } catch (error) {
                }
            };

            socketRef.current = socket;
        } catch (error) {
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
