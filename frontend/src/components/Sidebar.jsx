import { NavLink } from 'react-router-dom';
import { FiHome, FiUploadCloud, FiList, FiShield } from 'react-icons/fi';
import clsx from 'clsx';

const Sidebar = () => {
    const role = localStorage.getItem('role');

    const navItems = [
        ...(role === 'admin'
            ? [
                { name: 'Admin Dashboard', path: '/admin-dashboard', icon: FiHome },
                { name: 'Verify Media', path: '/verify-media', icon: FiShield },
                { name: 'Workspace Docs', path: '/workspace-docs', icon: FiList }
            ]
            : [
                { name: 'Dashboard', path: '/dashboard', icon: FiHome },
                { name: 'Upload Media', path: '/upload', icon: FiUploadCloud },
                { name: 'My Uploads', path: '/my-uploads', icon: FiList },
                { name: 'Workspace Docs', path: '/workspace-docs', icon: FiList }
            ]
        )
    ];

    return (
        <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-[calc(100vh-64px)] hidden md:block transition-colors duration-300">
            <div className="p-4 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            clsx(
                                'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                                isActive
                                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 shadow-sm'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-gray-200'
                            )
                        }
                    >
                        <item.icon className="w-5 h-5" />
                        {item.name}
                    </NavLink>
                ))}
            </div>
        </aside>
    );
};

export default Sidebar;
