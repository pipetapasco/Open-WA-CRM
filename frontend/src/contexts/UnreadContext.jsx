import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { getConversations } from '../services/whatsappService';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat/inbox/';

const UnreadContext = createContext({
    totalUnread: 0,
    refreshUnreadCount: () => { },
    incrementUnread: () => { },
    decrementUnread: () => { },
});

export function UnreadProvider({ children }) {
    const [totalUnread, setTotalUnread] = useState(0);
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    // Calcular el total de mensajes no leídos
    const refreshUnreadCount = useCallback(async () => {
        try {
            const conversations = await getConversations();
            const total = conversations.reduce((sum, conv) => sum + (conv.unread_count || 0), 0);
            setTotalUnread(total);
        } catch (error) {
        }
    }, []);

    // Incrementar contador cuando llega un mensaje nuevo
    const incrementUnread = useCallback((count = 1) => {
        setTotalUnread((prev) => prev + count);
    }, []);

    // Decrementar cuando se marcan como leídos
    const decrementUnread = useCallback((count) => {
        setTotalUnread((prev) => Math.max(0, prev - count));
    }, []);

    // Conectar WebSocket directamente en el provider (sin usar el hook)
    useEffect(() => {
        const connect = () => {
            if (socketRef.current?.readyState === WebSocket.OPEN) {
                return;
            }

            try {
                const socket = new WebSocket(WS_URL);

                socket.onopen = () => {
                };

                socket.onclose = (event) => {
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
                        // Solo nos interesa incrementar cuando llega un mensaje entrante nuevo
                        if (data.type === 'new_message' && data.message?.direction === 'incoming') {
                            setTotalUnread((prev) => prev + 1);
                        }
                    } catch (error) {
                    }
                };

                socketRef.current = socket;
            } catch (error) {
            }
        };

        // Cargar conteo inicial
        refreshUnreadCount();
        // Conectar WebSocket
        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, [refreshUnreadCount]);

    return (
        <UnreadContext.Provider
            value={{
                totalUnread,
                refreshUnreadCount,
                incrementUnread,
                decrementUnread,
            }}
        >
            {children}
        </UnreadContext.Provider>
    );
}

export function useUnreadCount() {
    return useContext(UnreadContext);
}
