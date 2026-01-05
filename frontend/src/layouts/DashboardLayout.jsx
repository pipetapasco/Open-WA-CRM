import { NavLink, Outlet } from 'react-router-dom';
import { MessageSquare, Users, Settings, Menu, X, LogOut } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useUnreadCount } from '../contexts/UnreadContext';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
    { to: '/inbox', icon: MessageSquare, label: 'Inbox' },
    { to: '/contacts', icon: Users, label: 'Contactos' },
    { to: '/settings', icon: Settings, label: 'Configuración' },
];

export default function DashboardLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [isMobile, setIsMobile] = useState(false);
    const { totalUnread } = useUnreadCount();
    const { user, logout } = useAuth();

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 640);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    const effectiveSidebarOpen = isMobile ? false : sidebarOpen;

    const handleLogout = () => {
        logout();
    };

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <aside
                className={`${effectiveSidebarOpen ? 'w-64' : 'w-16'
                    } bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out`}
            >
                {/* Logo / Toggle */}
                <div className="h-16 flex items-center justify-between px-4 border-b border-gray-100">
                    {effectiveSidebarOpen && (
                        <span className="text-xl font-semibold text-gray-800">
                            Open<span className="text-blue-600">WA</span>
                        </span>
                    )}
                    {!isMobile && (
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
                        >
                            {effectiveSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                        </button>
                    )}
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-4 px-2">
                    <ul className="space-y-1">
                        {navItems.map((item) => (
                            <li key={item.to}>
                                <NavLink
                                    to={item.to}
                                    className={({ isActive }) =>
                                        `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive
                                            ? 'bg-blue-50 text-blue-600 font-medium'
                                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                                        }`
                                    }
                                >
                                    <div className="relative">
                                        <item.icon size={20} />
                                        {item.to === '/inbox' && totalUnread > 0 && (
                                            <span className="absolute -top-2 -right-2 min-w-[18px] h-[18px] flex items-center justify-center px-1 text-[10px] font-bold text-white bg-red-500 rounded-full">
                                                {totalUnread > 99 ? '99+' : totalUnread}
                                            </span>
                                        )}
                                    </div>
                                    {effectiveSidebarOpen && (
                                        <span className="flex-1">{item.label}</span>
                                    )}
                                    {effectiveSidebarOpen && item.to === '/inbox' && totalUnread > 0 && (
                                        <span className="px-2 py-0.5 text-xs font-bold text-white bg-blue-500 rounded-full">
                                            {totalUnread > 99 ? '99+' : totalUnread}
                                        </span>
                                    )}
                                </NavLink>
                            </li>
                        ))}
                    </ul>
                </nav>

                {/* Footer with user info and logout */}
                <div className="p-4 border-t border-gray-100">
                    {effectiveSidebarOpen ? (
                        <div className="space-y-3">
                            {user && (
                                <div className="text-sm text-gray-600">
                                    <p className="font-medium text-gray-800">{user.username}</p>
                                    <p className="text-xs text-gray-400 truncate">{user.email}</p>
                                </div>
                            )}
                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            >
                                <LogOut size={18} />
                                <span>Cerrar Sesión</span>
                            </button>
                            <p className="text-xs text-gray-400">Open-WA CRM v1.0</p>
                        </div>
                    ) : (
                        <button
                            onClick={handleLogout}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Cerrar Sesión"
                        >
                            <LogOut size={20} />
                        </button>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <Outlet />
            </main>
        </div>
    );
}

