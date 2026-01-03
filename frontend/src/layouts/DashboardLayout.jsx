import { NavLink, Outlet } from 'react-router-dom';
import { MessageSquare, Users, Settings, Menu, X } from 'lucide-react';
import { useState } from 'react';

const navItems = [
    { to: '/inbox', icon: MessageSquare, label: 'Inbox' },
    { to: '/contacts', icon: Users, label: 'Contactos' },
    { to: '/settings', icon: Settings, label: 'Configuración' },
];

export default function DashboardLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <aside
                className={`${sidebarOpen ? 'w-64' : 'w-16'
                    } bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out`}
            >
                {/* Logo / Toggle */}
                <div className="h-16 flex items-center justify-between px-4 border-b border-gray-100">
                    {sidebarOpen && (
                        <span className="text-xl font-semibold text-gray-800">
                            Open<span className="text-blue-600">WA</span>
                        </span>
                    )}
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
                    >
                        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
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
                                    <item.icon size={20} />
                                    {sidebarOpen && <span>{item.label}</span>}
                                </NavLink>
                            </li>
                        ))}
                    </ul>
                </nav>

                {/* Footer */}
                {sidebarOpen && (
                    <div className="p-4 border-t border-gray-100">
                        <p className="text-xs text-gray-400">Open-WA CRM v1.0</p>
                    </div>
                )}
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <Outlet />
            </main>
        </div>
    );
}
