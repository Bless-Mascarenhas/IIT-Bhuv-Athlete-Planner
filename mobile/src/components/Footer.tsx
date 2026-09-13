import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ListTodo, Bot, CalendarDays, User } from 'lucide-react';

export default function Footer() {
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/planner', label: 'Planner', icon: <ListTodo size={20} /> },
    { path: '/chat', label: 'Chat', icon: <Bot size={24} />, isCenter: true },
    { path: '/calendar', label: 'Calendar', icon: <CalendarDays size={20} /> },
    { path: '/settings', label: 'Settings', icon: <User size={20} /> },
  ];

  return (
    <footer
      style={{
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        padding: '0.5rem 0.25rem',
        backgroundColor: 'var(--bg)',
        boxShadow: '0 -4px 14px rgba(163, 177, 198, 0.35)',
        zIndex: 20,
        position: 'relative',
        paddingBottom: 'calc(0.65rem + env(safe-area-inset-bottom))',
        borderTop: '1px solid rgba(255, 255, 255, 0.4)',
      }}
    >
      {navItems.map((item) => {
        if (item.isCenter) {
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `center-nav-btn ${isActive ? 'active' : ''}`}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textDecoration: 'none',
                marginTop: '-18px',
                position: 'relative',
              }}
            >
              {({ isActive }) => (
                <>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      backgroundColor: isActive ? '#fc5200' : 'var(--bg)',
                      color: isActive ? '#ffffff' : '#fc5200',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: isActive
                        ? '0 6px 14px rgba(252, 82, 0, 0.45)'
                        : '4px 4px 8px rgba(163,177,198,0.7), -4px -4px 8px rgba(255,255,255,0.8)',
                      transition: 'all 0.2s ease',
                      border: isActive ? '2px solid #ffffff' : '2px solid rgba(252, 82, 0, 0.2)',
                    }}
                  >
                    {item.icon}
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: '700',
                      marginTop: '3px',
                      color: isActive ? '#fc5200' : '#636e72',
                      letterSpacing: '-0.2px',
                    }}
                  >
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          );
        }

        return (
          <NavLink
            key={item.path}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textDecoration: 'none',
              padding: '0.35rem 0.6rem',
              borderRadius: '12px',
              color: isActive ? '#fc5200' : '#7f8c8d',
              transition: 'all 0.15s ease',
            })}
          >
            {({ isActive }) => (
              <>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '4px',
                    borderRadius: '8px',
                    boxShadow: isActive
                      ? 'inset 2px 2px 4px rgba(163,177,198,0.5), inset -2px -2px 4px rgba(255,255,255,0.8)'
                      : 'none',
                  }}
                >
                  {item.icon}
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: isActive ? '700' : '500',
                    marginTop: '2px',
                    color: isActive ? '#fc5200' : '#636e72',
                  }}
                >
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        );
      })}
    </footer>
  );
}
