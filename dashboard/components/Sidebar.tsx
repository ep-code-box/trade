
import React from 'react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  basketCount?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, basketCount = 0 }) => {
  const links = [
    { to: '/', label: '시장 개요', icon: '📊' },
    { to: '/account', label: '내 계좌 & 트레이딩', icon: '💎' },
    { to: '/basket', label: '장바구니 (Target)', icon: '🛒', badge: basketCount },
    { to: '/track1', label: '트랙 1: 주도주', icon: '🚀' },
    { to: '/trackex', label: '트랙 EX: 모멘텀', icon: '⚡' },
    { to: '/track2', label: '트랙 2: 배당주', icon: '💰' },
  ];

  return (
    <aside className={`
      fixed inset-y-0 left-0 w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col gap-8 z-50 transition-transform duration-300 ease-in-out md:static md:translate-x-0
      ${isOpen ? 'translate-x-0 shadow-2xl shadow-blue-500/10' : '-translate-x-full'}
    `}>
      <div className="flex items-center justify-between md:hidden">
        <span className="text-blue-500 font-bold tracking-tighter text-lg">TrendHunter</span>
        <button onClick={onClose} className="p-1 text-slate-500 hover:text-white">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-2 mt-4 md:mt-0">
        <p className="text-[10px] font-bold text-slate-600 uppercase tracking-[0.2em] px-3 pb-3">NAVIGATION</p>
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            onClick={() => onClose()}
            className={({ isActive }) => 
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all relative ${
                isActive 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/30' 
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`
            }
          >
            <span className="text-xl">{link.icon}</span>
            <span className="font-semibold text-sm flex-1">{link.label}</span>
            {link.badge !== undefined && link.badge > 0 && (
              <span className="bg-emerald-500 text-white text-[10px] px-1.5 py-0.5 rounded-md font-bold">
                {link.badge}
              </span>
            )}
          </NavLink>
        ))}
      </div>

      <div className="mt-auto space-y-4">
        <NavLink
          to="/settings"
          onClick={() => onClose()}
          className={({ isActive }) => 
            `flex items-center gap-3 px-4 py-3 rounded-xl transition-all border ${
              isActive 
                ? 'bg-slate-800 border-blue-500/50 text-white' 
                : 'text-slate-500 border-transparent hover:bg-slate-800/50 hover:text-slate-300'
            }`
          }
        >
          <span className="text-xl">⚙️</span>
          <span className="font-semibold text-sm">시스템 설정</span>
        </NavLink>

        <div className="bg-slate-800/30 p-5 rounded-2xl border border-slate-700/40 backdrop-blur-sm">
          <h4 className="text-xs font-bold text-blue-400 mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
            SYSTEM TRADING
          </h4>
          <p className="text-[10px] text-slate-500 leading-relaxed font-medium">
            장바구니 담긴 {basketCount}개 종목<br/>
            실시간 진입 타점 감시 중.
          </p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
