import React from 'react';
import { MessageSquare, Layers, Database, Sparkles, Rocket, Package, Store, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Link } from 'react-router-dom';

interface SidebarProps {
  activeSection: string;
  setActiveSection: (section: string) => void;
}

const Sidebar = ({ activeSection, setActiveSection }: SidebarProps) => {
  const menuItems = [
    {
      id: 'prompt-schema',
      label: 'Task Definition',
      icon: MessageSquare,
      description: 'Natural language dialogue'
    },
    {
      id: 'model-recommend',
      label: 'Model Selection',
      icon: Layers,
      description: 'Smart recommendations'
    },
    {
      id: 'data-builder',
      label: 'Data Builder',
      icon: Database,
      description: 'Multi-source data'
    },
    {
      id: 'data-engine',
      label: 'DFE Engine',
      icon: Sparkles,
      description: 'Data fusion & alignment'
    },
    {
      id: 'model-training',
      label: 'Training Center',
      icon: Rocket,
      description: 'Fine-tune models'
    },
    {
      id: 'model-deploy',
      label: 'Deployment',
      icon: Package,
      description: 'Export & API'
    },
    {
      id: 'model-market',
      label: 'Marketplace',
      icon: Store,
      description: 'Share models'
    }
  ];

  return (
    <aside className="w-72 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 flex-1 overflow-y-auto">
        {/* Logo */}
        <div className="mb-8">
        {/* Logo Section */}
        <Link to="/" className="flex items-center gap-4 mb-8">
            <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">M</span>
          </div>
          <div>
              <h2 className="font-semibold text-gray-900 text-lg">Metra</h2>
              <p className="text-xs text-gray-500">AI Training Platform</p>
          </div>
        </Link>

          {/* Progress */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <span className="text-sm text-gray-500">2/7</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-gray-900 h-2 rounded-full transition-all duration-300" style={{ width: '28.5%' }}></div>
            </div>
          </div>

          {/* Menu Items */}
          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-all duration-200 group ${
                    isActive 
                      ? 'bg-gray-900 text-white' 
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                    <div>
                      <div className={`font-medium ${isActive ? 'text-white' : 'text-gray-900'}`}>
                        {item.label}
                      </div>
                      <div className={`text-xs ${isActive ? 'text-gray-300' : 'text-gray-500'}`}>
                        {item.description}
                      </div>
                  </div>
                  </div>
                </button>
              );
            })}
          </nav>
          </div>

        {/* User Section */}
        <div className="p-6 border-t border-gray-200">
              <button
                onClick={() => setActiveSection('profile')}
            className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="h-5 w-5 text-gray-600" />
                </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">John Doe</div>
              <div className="text-xs text-gray-500">john@example.com</div>
            </div>
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
