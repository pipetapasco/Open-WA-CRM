import { Users } from 'lucide-react';

export default function ContactsPage() {
    return (
        <div className="p-6 lg:p-8">
            <div className="flex items-center gap-3 mb-6">
                <Users size={28} className="text-blue-600" />
                <h1 className="text-2xl font-bold text-gray-900">Contactos</h1>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                <p className="text-gray-500">Próximamente: Lista de contactos de WhatsApp</p>
            </div>
        </div>
    );
}
