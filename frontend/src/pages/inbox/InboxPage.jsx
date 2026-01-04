import { useState, useEffect, useRef, useCallback, Fragment } from 'react';
import {
    MessageSquare,
    Send,
    Phone,
    MoreVertical,
    Search,
    Wifi,
    WifiOff,
    Loader2,
    Check,
    CheckCheck,
    FileText,
    Download,
    Image as ImageIcon,
    Music,
    Play,
    Pause,
    Volume2,
    VolumeX,
    UserPlus,
    Trash2,
    X,
    Edit2,
    AlertTriangle,
    FileStack,
    Paperclip,
    Mic,
    StopCircle,
    Sparkles
} from 'lucide-react';
import useChatWebSocket from '../../hooks/useChatWebSocket';
import { useUnreadCount } from '../../contexts/UnreadContext';
import {
    getConversations,
    getMessages,
    sendMessage,
    markAsRead,
    deleteConversation,
    updateContact,
    sendTemplateMessage,
    uploadMedia,
    sendMediaMessage
} from '../../services/whatsappService';
import SendTemplateModal from '../../components/modals/SendTemplateModal';

// ============== HELPER FUNCTIONS ==============
const getDateLabel = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) return 'Hoy';
    if (date.toDateString() === yesterday.toDateString()) return 'Ayer';

    return date.toLocaleDateString('es-ES', {
        weekday: 'long',
        day: 'numeric',
        month: 'long'
    });
};

const getMediaUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    try {
        const urlObj = new URL(apiUrl);
        return `${urlObj.origin}${url.startsWith('/') ? '' : '/'}${url}`;
    } catch (e) {
        return `http://localhost:8000${url.startsWith('/') ? '' : '/'}${url}`;
    }
};

// ============== DATE SEPARATOR COMPONENT ==============
function DateSeparator({ date }) {
    return (
        <div className="flex items-center justify-center my-4">
            <span className="px-4 py-1.5 bg-white/80 backdrop-blur-sm text-gray-600 text-xs font-medium rounded-full shadow-sm border border-gray-100">
                {getDateLabel(date)}
            </span>
        </div>
    );
}

// ============== CHAT LIST COMPONENT ==============
function ChatList({ conversations, selectedChat, onSelectChat, loading }) {
    const formatTime = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();

        if (isToday) {
            return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
        }
        return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
        );
    }

    if (conversations.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 p-4">
                <MessageSquare size={48} className="mb-4 text-gray-300" />
                <p className="text-center">No hay conversaciones</p>
                <p className="text-sm text-center">Los chats aparecerán aquí cuando recibas mensajes</p>
            </div>
        );
    }

    return (
        <div className="overflow-y-auto h-full">
            {conversations.map((chat) => (
                <div
                    key={chat.id}
                    onClick={() => onSelectChat(chat)}
                    className={`flex items-center gap-3 p-4 cursor-pointer border-b border-gray-100 hover:bg-gray-50 transition-colors ${selectedChat?.id === chat.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                        }`}
                >
                    {/* Avatar */}
                    <div className="relative flex-shrink-0">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold">
                            {chat.contact?.profile_picture_url ? (
                                <img
                                    src={chat.contact.profile_picture_url}
                                    alt={chat.contact.name}
                                    className="w-12 h-12 rounded-full object-cover"
                                />
                            ) : (
                                <span>{chat.contact?.name?.charAt(0)?.toUpperCase() || '?'}</span>
                            )}
                        </div>
                        {/* Online indicator */}
                        {chat.status === 'open' && (
                            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></span>
                        )}
                    </div>

                    {/* Chat Info */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                            <h4 className="font-semibold text-gray-900 truncate">
                                {chat.contact?.name || chat.contact?.phone_number || 'Contacto'}
                            </h4>
                            <span className="text-xs text-gray-500 flex-shrink-0">
                                {formatTime(chat.last_message_at)}
                            </span>
                        </div>
                        <div className="flex items-center justify-between mt-1">
                            <p className="text-sm text-gray-500 truncate">
                                {chat.last_message || 'Sin mensajes'}
                            </p>
                            {chat.unread_count > 0 && (
                                <span className="flex-shrink-0 ml-2 px-2 py-0.5 text-xs font-bold text-white bg-blue-500 rounded-full">
                                    {chat.unread_count}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

// ============== CUSTOM AUDIO PLAYER ==============
const formatDuration = (seconds) => {
    if (!seconds || !isFinite(seconds) || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

function CustomAudioPlayer({ src, isOutgoing }) {
    const audioRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);

    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        const setAudioData = () => {
            if (audio.duration && isFinite(audio.duration)) {
                setDuration(audio.duration);
            }
        };

        const setAudioTime = () => setCurrentTime(audio.currentTime);
        const onEnded = () => setIsPlaying(false);
        const onError = () => { };

        // loadedmetadata es más confiable que loadeddata para obtener la duración
        audio.addEventListener('loadedmetadata', setAudioData);
        audio.addEventListener('durationchange', setAudioData);
        audio.addEventListener('timeupdate', setAudioTime);
        audio.addEventListener('ended', onEnded);
        audio.addEventListener('error', onError);

        // Si el audio ya tiene metadatos cargados (por cache del navegador)
        if (audio.readyState >= 1 && audio.duration && isFinite(audio.duration)) {
            setDuration(audio.duration);
        }

        return () => {
            audio.removeEventListener('loadedmetadata', setAudioData);
            audio.removeEventListener('durationchange', setAudioData);
            audio.removeEventListener('timeupdate', setAudioTime);
            audio.removeEventListener('ended', onEnded);
            audio.removeEventListener('error', onError);
        };
    }, [src]);

    const togglePlay = () => {
        if (!audioRef.current) return;
        if (audioRef.current.paused) {
            audioRef.current.play().catch(() => { });
            setIsPlaying(true);
        } else {
            audioRef.current.pause();
            setIsPlaying(false);
        }
    };

    const handleSeek = (e) => {
        const time = Number(e.target.value);
        if (audioRef.current) {
            audioRef.current.currentTime = time;
            setCurrentTime(time);
        }
    };

    return (
        <div className={`flex flex-col justify-center w-[240px] p-2`}>
            <div className="flex items-center gap-3">
                <button
                    onClick={togglePlay}
                    className={`w-10 h-10 flex items-center justify-center rounded-full transition-all shadow-sm flex-shrink-0 ${isOutgoing
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
                        }`}
                >
                    {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
                </button>

                <div className="flex-1 min-w-0 flex flex-col justify-center gap-1.5">
                    <input
                        type="range"
                        min="0"
                        max={duration || 100}
                        step="0.1"
                        value={currentTime}
                        onChange={handleSeek}
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-0 [&::-webkit-slider-thumb]:shadow-sm [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0"
                        style={{
                            background: `linear-gradient(to right, ${isOutgoing ? '#bfdbfe' : '#3b82f6'} ${(currentTime / (duration || 1)) * 100}%, ${isOutgoing ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'} ${(currentTime / (duration || 1)) * 100}%)`,
                            '--thumb-color': isOutgoing ? '#bfdbfe' : '#3b82f6'
                        }}
                    />
                    <style>{`
                        input[type="range"]::-webkit-slider-thumb {
                            background-color: ${isOutgoing ? '#bfdbfe' : '#3b82f6'};
                        }
                        input[type="range"]::-moz-range-thumb {
                            background-color: ${isOutgoing ? '#bfdbfe' : '#3b82f6'};
                        }
                    `}</style>
                    <div className={`flex justify-between text-[10px] font-medium leading-none tracking-wide ${isOutgoing ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                        <span>{formatDuration(currentTime)}</span>
                        <span>{duration > 0 ? formatDuration(duration) : '--:--'}</span>
                    </div>
                </div>
            </div>

            <audio ref={audioRef} src={src} preload="metadata" className="hidden" />
        </div>
    );
}

// ============== MESSAGE BUBBLE COMPONENT ==============
function MessageBubble({ message }) {
    const isOutgoing = message.direction === 'outgoing';

    const StatusIcon = () => {
        switch (message.delivery_status) {
            case 'read':
                return <CheckCheck size={14} className="text-cyan-300" />;
            case 'delivered':
                return <CheckCheck size={14} className="text-white/70" />;
            case 'sent':
                return <Check size={14} className="text-white/70" />;
            default:
                return <Loader2 size={14} className="text-white/50 animate-spin" />;
        }
    };

    // Helper para determinar si mostrar el caption
    const shouldShowCaption = () => {
        if (!message.body) return false;
        const trimmedBody = message.body.trim();
        // Ocultar si es igual a los placeholders por defecto (case insensitive)
        const placeholders = ['[IMAGE]', '[VIDEO]', '[AUDIO]', '[DOCUMENT]', '[STICKER]', '[LOCATION]', '[CONTACTS]'];
        return !placeholders.includes(trimmedBody.toUpperCase());
    };

    // Renderizar contenido según el tipo de mensaje
    const renderContent = () => {
        const mediaUrl = getMediaUrl(message.media_url);

        switch (message.message_type) {
            case 'image':
                return (
                    <div className="mb-1">
                        <a href={mediaUrl} target="_blank" rel="noopener noreferrer">
                            <img
                                src={mediaUrl}
                                alt="Imagen"
                                className="max-h-[300px] rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                                loading="lazy"
                            />
                        </a>
                        {shouldShowCaption() && (
                            <p className="text-sm whitespace-pre-wrap break-words mt-2">
                                {message.body}
                            </p>
                        )}
                    </div>
                );

            case 'video':
                return (
                    <div className="mb-1">
                        <video
                            src={mediaUrl}
                            controls
                            className="max-h-[300px] rounded-lg"
                            preload="metadata"
                        />
                        {shouldShowCaption() && (
                            <p className="text-sm whitespace-pre-wrap break-words mt-2">
                                {message.body}
                            </p>
                        )}
                    </div>
                );

            case 'audio':
                return (
                    <div className="mb-1">
                        <CustomAudioPlayer src={mediaUrl} isOutgoing={isOutgoing} />
                        {shouldShowCaption() && (
                            <p className="text-sm whitespace-pre-wrap break-words mt-2">
                                {message.body}
                            </p>
                        )}
                    </div>
                );

            case 'document':
                return (
                    <a
                        href={mediaUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        className={`flex items-center gap-3 p-3 rounded-lg mb-1 transition-colors ${isOutgoing
                            ? 'bg-blue-400/30 hover:bg-blue-400/40'
                            : 'bg-white hover:bg-gray-50 shadow-sm border border-gray-100'
                            }`}
                    >
                        <div className={`p-2 rounded-lg ${isOutgoing ? 'bg-blue-400/50' : 'bg-gray-200'}`}>
                            <FileText size={24} className={isOutgoing ? 'text-white' : 'text-gray-600'} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium truncate ${isOutgoing ? 'text-white' : 'text-gray-800'}`}>
                                {message.body || 'Documento'}
                            </p>
                            <p className={`text-xs ${isOutgoing ? 'text-blue-200' : 'text-gray-500'}`}>
                                Toca para descargar
                            </p>
                        </div>
                        <Download size={18} className={isOutgoing ? 'text-white/70' : 'text-gray-500'} />
                    </a>
                );

            case 'sticker':
                return (
                    <div className="mb-1">
                        <img
                            src={mediaUrl}
                            alt="Sticker"
                            className="max-h-[150px] max-w-[150px]"
                            loading="lazy"
                        />
                    </div>
                );

            case 'location':
                return (
                    <div className={`p-3 rounded-lg mb-1 shadow-sm border border-gray-100 ${isOutgoing ? 'bg-blue-400/30 border-transparent' : 'bg-white'}`}>
                        <p className={`text-sm ${isOutgoing ? 'text-white' : 'text-gray-800'}`}>
                            📍 Ubicación compartida
                        </p>
                        {message.body && (
                            <p className={`text-xs mt-1 ${isOutgoing ? 'text-blue-200' : 'text-gray-500'}`}>
                                {message.body}
                            </p>
                        )}
                    </div>
                );

            case 'contacts':
                return (
                    <div className={`p-3 rounded-lg mb-1 shadow-sm border border-gray-100 ${isOutgoing ? 'bg-blue-400/30 border-transparent' : 'bg-white'}`}>
                        <p className={`text-sm ${isOutgoing ? 'text-white' : 'text-gray-800'}`}>
                            👤 Contacto compartido
                        </p>
                    </div>
                );

            default: // text
                return (
                    <p className="text-sm whitespace-pre-wrap break-words">
                        {message.body || `[${message.message_type}]`}
                    </p>
                );
        }
    };

    return (
        <div className={`flex ${isOutgoing ? 'justify-end' : 'justify-start'} mb-3`}>
            <div
                className={`max-w-[70%] rounded-2xl px-4 py-2 shadow-sm ${isOutgoing
                    ? 'bg-blue-500 text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-900 rounded-bl-md border border-gray-200'
                    }`}
            >
                {/* Message content */}
                {renderContent()}

                {/* Time and status */}
                <div className={`flex items-center justify-end gap-1 mt-1 text-xs ${isOutgoing ? 'text-blue-100' : 'text-gray-400'
                    }`}>
                    <span>
                        {new Date(message.created_at).toLocaleTimeString('es-ES', {
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </span>
                    {isOutgoing && message.metadata?.ai_generated && (
                        <Sparkles size={12} className="text-purple-200 mx-0.5" title="Generado por IA" />
                    )}
                    {isOutgoing && <StatusIcon />}
                </div>
            </div>
        </div>
    );
}

// ============== CHAT WINDOW COMPONENT ==============
function ChatWindow({
    chat,
    messages,
    onSendMessage,
    loading,
    sendingMessage,
    onDeleteConversation,
    onUpdateContactName,
    onSendTemplate,
    onTemplateSuccess,
    onMediaSent
}) {
    const [inputText, setInputText] = useState('');
    const [showMenu, setShowMenu] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [showEditNameModal, setShowEditNameModal] = useState(false);
    const [newContactName, setNewContactName] = useState('');
    const [isSavingName, setIsSavingName] = useState(false);
    const [showTemplateModal, setShowTemplateModal] = useState(false);

    // Media & Recording State
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [previewFile, setPreviewFile] = useState(null); // New Preview State
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const timerRef = useRef(null);
    const fileInputRef = useRef(null);
    const isCancelledRef = useRef(false);

    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const menuRef = useRef(null);

    // Verificar si la ventana de 24h está abierta
    const canSendFreeMessage = chat?.can_send_free_message ?? true;

    // Recording Handlers
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];
            isCancelledRef.current = false;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                // Stop tracks cleanup
                stream.getTracks().forEach(track => track.stop());

                if (isCancelledRef.current) {
                    return;
                }

                // Process audio
                const blobSize = audioChunksRef.current.reduce((acc, chunk) => acc + chunk.size, 0);

                if (blobSize === 0) {
                    alert('Grabación vacía - por favor intenta de nuevo');
                    return;
                }

                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                const file = new File([audioBlob], 'voice_note.webm', { type: 'audio/webm' });

                await handleUploadAndSend(file, 'audio');
            };

            mediaRecorder.start(1000); // Collect data every second to ensure chunks
            setIsRecording(true);
            setRecordingTime(0);

            timerRef.current = setInterval(() => {
                setRecordingTime(prev => prev + 1);
            }, 1000);

        } catch (err) {
            alert('No se pudo acceder al micrófono. Verifica los permisos.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            if (mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stop();
            }
            clearInterval(timerRef.current);
            setIsRecording(false);
            // Processing happens in onstop
        }
    };

    const cancelRecording = () => {
        isCancelledRef.current = true;
        if (mediaRecorderRef.current) {
            if (mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stop();
            }
        }
        clearInterval(timerRef.current);
        setIsRecording(false);
        audioChunksRef.current = [];
    };

    // File Handling
    const handleFileSelect = async (e) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setPreviewFile(file); // Set for preview instead of sending immediately

            // Reset input so potential cancel & re-select works
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleUploadAndSend = async (file, type) => {
        setIsUploading(true);
        try {
            // 1. Upload
            const uploadResult = await uploadMedia(file);

            // 2. Send
            const newMessage = await sendMediaMessage(chat.id, {
                media_type: type,
                media_url: uploadResult.url,
                caption: type !== 'audio' ? inputText : ''
            });

            // 3. Notify Parent to update UI
            onMediaSent?.(newMessage);

            if (type !== 'audio') setInputText('');
            setPreviewFile(null); // Close preview

        } catch (err) {
            console.error('Error sending media:', err);
            alert(`Error al enviar archivo multimedia: ${err.message}`);
        } finally {
            setIsUploading(false);
        }
    };

    const handleSendPreview = async () => {
        if (!previewFile) return;

        // Determine type
        let type = 'document';
        if (previewFile.type.startsWith('image/')) type = 'image';
        else if (previewFile.type.startsWith('video/')) type = 'video';
        else if (previewFile.type.startsWith('audio/')) type = 'audio';

        await handleUploadAndSend(previewFile, type);
    };

    const handleCancelPreview = () => {
        setPreviewFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    // Cerrar menú al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowMenu(false);
            }
        };
        // Usar 'click' en lugar de 'mousedown' para que los botones del menú funcionen
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (inputText.trim() && !sendingMessage) {
            onSendMessage(inputText.trim());
            setInputText('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    if (!chat) {
        return (
            <div className="flex flex-col items-center justify-center h-full w-full bg-gray-50 text-gray-500">
                <MessageSquare size={64} className="mb-4 text-gray-300" />
                <h3 className="text-xl font-medium text-gray-600">Selecciona un chat</h3>
                <p className="text-sm mt-2">Elige una conversación para comenzar a chatear</p>
            </div>
        );
    }

    // Ordenar mensajes de más viejo a más nuevo para mostrar
    const sortedMessages = [...messages].sort(
        (a, b) => new Date(a.created_at) - new Date(b.created_at)
    );

    return (
        <div className="flex flex-col h-full w-full bg-gray-50">
            {/* Chat Header */}
            <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold">
                        {chat.contact?.profile_picture_url ? (
                            <img
                                src={chat.contact.profile_picture_url}
                                alt={chat.contact.name}
                                className="w-10 h-10 rounded-full object-cover"
                            />
                        ) : (
                            <span>{chat.contact?.name?.charAt(0)?.toUpperCase() || '?'}</span>
                        )}
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900">
                            {chat.contact?.name || 'Contacto'}
                        </h3>
                        <p className="text-sm text-gray-500 flex items-center gap-1">
                            <Phone size={12} />
                            {chat.contact?.phone_number}
                        </p>
                    </div>
                </div>

                {/* Menu Button with Dropdown */}
                <div className="relative" ref={menuRef}>
                    <button
                        onClick={() => setShowMenu(!showMenu)}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <MoreVertical size={20} className="text-gray-500" />
                    </button>

                    {/* Dropdown Menu */}
                    {showMenu && (
                        <div className="absolute right-0 top-full mt-1 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                            <button
                                type="button"
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setShowMenu(false);
                                    setNewContactName(chat.contact?.name || '');
                                    setShowEditNameModal(true);
                                }}
                                className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors"
                            >
                                <Edit2 size={18} className="text-blue-500" />
                                Editar nombre
                            </button>
                            <button
                                type="button"
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setShowMenu(false);
                                    setShowTemplateModal(true);
                                }}
                                className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors"
                            >
                                <FileStack size={18} className="text-green-500" />
                                Enviar Plantilla
                            </button>
                            <div className="border-t border-gray-100 my-1"></div>
                            <button
                                type="button"
                                onClick={async (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    const confirmed = window.confirm('¿Estás seguro de eliminar esta conversación? Se eliminarán todos los mensajes y archivos multimedia.');
                                    if (confirmed) {
                                        setIsDeleting(true);
                                        setShowMenu(false);
                                        try {
                                            if (onDeleteConversation) {
                                                await onDeleteConversation(chat.id);
                                            }
                                        } catch (err) {
                                        } finally {
                                            setIsDeleting(false);
                                        }
                                    }
                                }}
                                disabled={isDeleting}
                                className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors disabled:opacity-50"
                            >
                                {isDeleting ? (
                                    <Loader2 size={18} className="animate-spin" />
                                ) : (
                                    <Trash2 size={18} />
                                )}
                                Eliminar conversación
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Messages Container */}
            <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto p-4"
                style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%239C92AC\' fill-opacity=\'0.05\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")' }}
            >
                {loading ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                    </div>
                ) : sortedMessages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <p>No hay mensajes aún</p>
                        <p className="text-sm">Envía el primer mensaje</p>
                    </div>
                ) : (
                    <>
                        {sortedMessages.map((msg, index) => {
                            // Mostrar separador de fecha si es el primer mensaje o si cambió el día
                            const showDateSeparator = index === 0 ||
                                new Date(msg.created_at).toDateString() !==
                                new Date(sortedMessages[index - 1].created_at).toDateString();

                            return (
                                <Fragment key={msg.id}>
                                    {showDateSeparator && <DateSeparator date={msg.created_at} />}
                                    <MessageBubble message={msg} />
                                </Fragment>
                            );
                        })}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            {/* Message Input or 24h Warning */}

            {canSendFreeMessage ? (
                <div className="p-4 bg-white border-t border-gray-200">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        className="hidden"
                        accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.txt"
                    />

                    {previewFile ? (
                        <div className="flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div className="flex items-center gap-4 mb-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
                                {previewFile.type.startsWith('image/') ? (
                                    <img
                                        src={URL.createObjectURL(previewFile)}
                                        alt="Preview"
                                        className="w-16 h-16 object-cover rounded-md"
                                    />
                                ) : (
                                    <div className="w-16 h-16 bg-blue-100 rounded-md flex items-center justify-center text-blue-500">
                                        <FileStack size={32} />
                                    </div>
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-gray-900 truncate">{previewFile.name}</p>
                                    <p className="text-xs text-gray-500">{(previewFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleCancelPreview}
                                    className="p-3 text-gray-500 hover:bg-gray-100 rounded-full transition-colors"
                                    title="Cancelar"
                                >
                                    <X size={24} />
                                </button>

                                <input
                                    type="text"
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') handleSendPreview();
                                    }}
                                    placeholder="Añadir un comentario..."
                                    className="flex-1 px-4 py-3 bg-gray-100 border-0 rounded-full focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                                    disabled={isUploading}
                                    autoFocus
                                />

                                <button
                                    onClick={handleSendPreview}
                                    disabled={isUploading}
                                    className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
                                >
                                    {isUploading ? (
                                        <Loader2 size={20} className="animate-spin" />
                                    ) : (
                                        <Send size={20} />
                                    )}
                                </button>
                            </div>
                        </div>
                    ) : isRecording ? (
                        <div className="flex items-center gap-4 animate-in fade-in duration-200">
                            <div className="flex-1 flex items-center gap-3 px-4 py-3 bg-red-50 rounded-full text-red-600">
                                <span className="animate-pulse font-medium">Grabando...</span>
                                <span className="font-mono ml-auto">{formatDuration(recordingTime)}</span>
                            </div>
                            <button
                                onClick={cancelRecording}
                                className="p-3 text-gray-500 hover:bg-gray-100 rounded-full transition-colors"
                            >
                                <X size={24} />
                            </button>
                            <button
                                onClick={stopRecording}
                                className="p-3 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors shadow-lg"
                            >
                                <Send size={20} />
                            </button>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isUploading || sendingMessage}
                                className="p-3 text-gray-500 hover:bg-gray-100 rounded-full transition-colors"
                            >
                                <Paperclip size={24} />
                            </button>

                            <input
                                type="text"
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Escribe un mensaje..."
                                className="flex-1 px-4 py-3 bg-gray-100 border-0 rounded-full focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                                disabled={sendingMessage || isUploading}
                            />

                            {inputText.trim() ? (
                                <button
                                    type="submit"
                                    disabled={!inputText.trim() || sendingMessage || isUploading}
                                    className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {sendingMessage || isUploading ? (
                                        <Loader2 size={20} className="animate-spin" />
                                    ) : (
                                        <Send size={20} />
                                    )}
                                </button>
                            ) : (
                                <button
                                    type="button"
                                    onClick={startRecording}
                                    disabled={sendingMessage || isUploading}
                                    className="p-3 text-gray-500 hover:bg-gray-100 rounded-full transition-colors"
                                >
                                    <Mic size={24} />
                                </button>
                            )}
                        </form>
                    )}
                </div>
            ) : (
                <div className="p-4 bg-amber-50 border-t border-amber-200">
                    <div className="flex items-start gap-3">
                        <AlertTriangle size={24} className="text-amber-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                            <p className="text-sm font-medium text-amber-800">
                                La ventana de 24 horas se ha cerrado
                            </p>
                            <p className="text-xs text-amber-600 mt-1">
                                Solo puedes enviar mensajes usando plantillas aprobadas por WhatsApp.
                            </p>
                        </div>
                        <button
                            onClick={() => setShowTemplateModal(true)}
                            className="px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 transition-colors flex items-center gap-2"
                        >
                            <FileStack size={16} />
                            Enviar Plantilla
                        </button>
                    </div>
                </div>
            )}

            {/* Modal para editar nombre */}
            {showEditNameModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                            <h3 className="text-lg font-semibold text-gray-900">Editar nombre del contacto</h3>
                            <button
                                onClick={() => setShowEditNameModal(false)}
                                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                            >
                                <X size={20} className="text-gray-500" />
                            </button>
                        </div>
                        <div className="px-6 py-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Nombre
                            </label>
                            <input
                                type="text"
                                value={newContactName}
                                onChange={(e) => setNewContactName(e.target.value)}
                                placeholder="Ingresa el nombre del contacto"
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                                autoFocus
                            />
                            <p className="mt-2 text-xs text-gray-500">
                                Teléfono: {chat.contact?.phone_number}
                            </p>
                        </div>
                        <div className="flex gap-3 px-6 py-4 bg-gray-50 border-t border-gray-100">
                            <button
                                onClick={() => setShowEditNameModal(false)}
                                className="flex-1 px-4 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={async () => {
                                    if (!newContactName.trim()) return;
                                    setIsSavingName(true);
                                    try {
                                        if (onUpdateContactName) {
                                            await onUpdateContactName(chat.contact?.id, newContactName.trim());
                                        }
                                        setShowEditNameModal(false);
                                    } catch (err) {
                                        alert('Error al actualizar el nombre');
                                    } finally {
                                        setIsSavingName(false);
                                    }
                                }}
                                disabled={isSavingName || !newContactName.trim()}
                                className="flex-1 px-4 py-2.5 text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                            >
                                {isSavingName ? (
                                    <>
                                        <Loader2 size={18} className="animate-spin" />
                                        Guardando...
                                    </>
                                ) : (
                                    'Guardar'
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Template Modal */}
            <SendTemplateModal
                isOpen={showTemplateModal}
                onClose={() => setShowTemplateModal(false)}
                accountId={chat.account_id}
                conversationId={chat.id}
                contactPhone={chat.contact?.phone_number}
                contactName={chat.contact?.name}
                onSuccess={(newMessage) => {
                    // El mensaje de template se añadirá via el reload del componente
                    onTemplateSuccess?.(newMessage);
                }}
            />
        </div>
    );
}

// ============== MAIN INBOX PAGE ==============
export default function InboxPage() {
    const [conversations, setConversations] = useState([]);
    const [selectedChat, setSelectedChat] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loadingChats, setLoadingChats] = useState(true);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [sendingMessage, setSendingMessage] = useState(false);

    // Context para contador global de no leídos
    const { decrementUnread, refreshUnreadCount } = useUnreadCount();

    // Ref para el audio de notificación
    const notificationAudioRef = useRef(null);

    // Inicializar audio de notificación
    useEffect(() => {
        notificationAudioRef.current = new Audio('/notification.mp3');
        notificationAudioRef.current.volume = 0.25;
    }, []);

    // Callback para nuevos mensajes via WebSocket
    const handleNewMessage = useCallback((newMessage) => {
        if (newMessage.direction === 'incoming') {
            notificationAudioRef.current?.play().catch(() => { });
        }

        // Actualizar la lista de conversaciones
        setConversations((prev) => {
            const conversationIndex = prev.findIndex(
                (c) => c.id === newMessage.conversation_id
            );

            if (conversationIndex === -1) {
                // Conversación no encontrada, recargar lista
                loadConversations();
                return prev;
            }

            const updated = [...prev];
            const conversation = { ...updated[conversationIndex] };

            // Actualizar last_message y timestamp
            conversation.last_message = newMessage.body || `[${newMessage.message_type}]`;
            conversation.last_message_at = newMessage.created_at;

            // Incrementar unread solo para mensajes entrantes y si no es el chat seleccionado
            if (newMessage.direction === 'incoming' && selectedChat?.id !== newMessage.conversation_id) {
                conversation.unread_count = (conversation.unread_count || 0) + 1;
            }

            // Remover de la posición actual
            updated.splice(conversationIndex, 1);
            // Agregar al inicio
            updated.unshift(conversation);

            return updated;
        });

        // Si el mensaje es del chat activo, agregarlo a la lista
        // (La deduplicación maneja los mensajes que enviamos nosotros manualmente)
        if (selectedChat?.id === newMessage.conversation_id) {
            setMessages((prev) => {
                // Evitar duplicados por ID
                if (prev.some((m) => m.id === newMessage.id)) {
                    return prev;
                }
                return [...prev, newMessage];
            });
        }
    }, [selectedChat]);

    // Callback para actualizaciones de estado via WebSocket
    const handleStatusUpdate = useCallback((statusUpdate) => {
        setMessages((prev) =>
            prev.map((msg) =>
                msg.id === statusUpdate.message_id
                    ? { ...msg, delivery_status: statusUpdate.delivery_status }
                    : msg
            )
        );
    }, []);

    // Conectar WebSocket
    const { isConnected } = useChatWebSocket({
        onNewMessage: handleNewMessage,
        onStatusUpdate: handleStatusUpdate,
    });

    // Cargar conversaciones
    const loadConversations = async () => {
        try {
            setLoadingChats(true);
            const data = await getConversations();
            setConversations(data);
        } catch (error) {
        } finally {
            setLoadingChats(false);
        }
    };

    // Cargar mensajes de un chat
    const loadMessages = async (conversationId) => {
        try {
            setLoadingMessages(true);
            const data = await getMessages(conversationId);
            // La API devuelve paginado, tomamos los results
            setMessages(data.results || data);
        } catch (error) {
            setMessages([]);
        } finally {
            setLoadingMessages(false);
        }
    };

    // Seleccionar chat
    const handleSelectChat = async (chat) => {
        setSelectedChat(chat);
        await loadMessages(chat.id);

        // Marcar como leídos
        if (chat.unread_count > 0) {
            try {
                await markAsRead(chat.id);
                // Actualizar contador local
                setConversations((prev) =>
                    prev.map((c) =>
                        c.id === chat.id ? { ...c, unread_count: 0 } : c
                    )
                );
                // Decrementar contador global
                decrementUnread(chat.unread_count);
            } catch (error) {
            }
        }
    };

    // Enviar mensaje
    const handleSendMessage = async (textOrMessage, isMedia = false) => {
        if (!selectedChat) return;

        setSendingMessage(true);
        try {
            let newMessage;
            if (isMedia) {
                newMessage = textOrMessage;
            } else {
                newMessage = await sendMessage(selectedChat.id, textOrMessage);
            }

            setMessages((prev) => [...prev, newMessage]);

            // Actualizar conversación
            setConversations((prev) => {
                const index = prev.findIndex((c) => c.id === selectedChat.id);
                if (index === -1) return prev;

                const updated = [...prev];
                const conversation = { ...updated[index] };
                conversation.last_message = newMessage.body || `[${newMessage.message_type}]`;
                conversation.last_message_at = newMessage.created_at;

                updated.splice(index, 1);
                updated.unshift(conversation);

                return updated;
            });
        } catch (error) {
            alert('Error al enviar el mensaje');
        } finally {
            setSendingMessage(false);
        }
    };

    // Eliminar conversación
    const handleDeleteConversation = async (conversationId) => {
        try {
            await deleteConversation(conversationId);
            // Remover de la lista de conversaciones
            setConversations((prev) => prev.filter((c) => c.id !== conversationId));
            // Si era el chat seleccionado, deseleccionar
            if (selectedChat?.id === conversationId) {
                setSelectedChat(null);
                setMessages([]);
            }
        } catch (error) {
            alert('Error al eliminar la conversación');
        }
    };

    // Actualizar nombre del contacto
    const handleUpdateContactName = async (contactId, newName) => {
        try {
            await updateContact(contactId, { name: newName });
            // Actualizar el estado local de las conversaciones
            setConversations((prev) =>
                prev.map((c) =>
                    c.contact?.id === contactId
                        ? { ...c, contact: { ...c.contact, name: newName } }
                        : c
                )
            );
            // Actualizar el chat seleccionado si corresponde
            if (selectedChat?.contact?.id === contactId) {
                setSelectedChat((prev) => ({
                    ...prev,
                    contact: { ...prev.contact, name: newName }
                }));
            }
        } catch (error) {
            throw error;
        }
    };

    // Cargar conversaciones al montar
    useEffect(() => {
        loadConversations();
    }, []);

    return (
        <div className="flex h-[calc(100vh-64px)] bg-gray-100">
            {/* Left Panel - Chat List */}
            <div className="w-full md:w-[350px] lg:w-[400px] flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-xl font-bold text-gray-900">Mensajes</h2>
                        <div className="flex items-center gap-2">
                            {isConnected ? (
                                <span className="flex items-center gap-1 text-xs text-green-600">
                                    <Wifi size={14} />
                                    En línea
                                </span>
                            ) : (
                                <span className="flex items-center gap-1 text-xs text-red-500">
                                    <WifiOff size={14} />
                                    Desconectado
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Search */}
                    <div className="relative">
                        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Buscar conversación..."
                            className="w-full pl-10 pr-4 py-2 bg-gray-100 border-0 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                </div>

                {/* Conversations List */}
                <ChatList
                    conversations={conversations}
                    selectedChat={selectedChat}
                    onSelectChat={handleSelectChat}
                    loading={loadingChats}
                />
            </div>

            {/* Right Panel - Chat Window */}
            <div className="flex-1 hidden md:flex">
                <ChatWindow
                    chat={selectedChat}
                    messages={messages}
                    onSendMessage={handleSendMessage}
                    loading={loadingMessages}
                    sendingMessage={sendingMessage}
                    onDeleteConversation={handleDeleteConversation}
                    onUpdateContactName={handleUpdateContactName}
                    onTemplateSuccess={(newMessage) => {
                        handleSendMessage(newMessage, true);
                    }}
                    onMediaSent={(msg) => handleSendMessage(msg, true)}
                />
            </div>

            {/* Mobile Chat Window (overlay) */}
            {selectedChat && (
                <div className="fixed inset-0 z-50 md:hidden">
                    <ChatWindow
                        chat={selectedChat}
                        messages={messages}
                        onSendMessage={handleSendMessage}
                        loading={loadingMessages}
                        sendingMessage={sendingMessage}
                        onDeleteConversation={handleDeleteConversation}
                        onUpdateContactName={handleUpdateContactName}
                        onTemplateSuccess={(newMessage) => {
                            handleSendMessage(newMessage, true);
                        }}
                        onMediaSent={(msg) => handleSendMessage(msg, true)}
                    />
                    <button
                        onClick={() => setSelectedChat(null)}
                        className="absolute top-4 left-4 p-2 bg-white rounded-full shadow-lg"
                    >
                        ← Volver
                    </button>
                </div>
            )}
        </div>
    );
}
