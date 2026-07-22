'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/lib/stores/auth.store';
import { Menu, X, User, LogOut, LayoutDashboard } from 'lucide-react';

export function Navbar() {
  const { isAuthenticated, user, clearAuth } = useAuthStore();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropOpen, setDropOpen] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);

  return (
    <nav
      style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: scrolled ? 'rgba(255,255,255,.97)' : 'rgba(255,255,255,.9)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #EDE5D8',
        transition: 'all .3s',
        boxShadow: scrolled ? '0 2px 20px rgba(0,0,0,.06)' : 'none',
      }}
    >
      <div
        style={{
          maxWidth: 1200, margin: '0 auto',
          padding: '0 1.5rem',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          height: 68,
        }}
      >
        {/* Logo */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: '#3D3022',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontWeight: 900, fontSize: 17,
          }}>R</div>
          <span style={{ fontSize: 18, fontWeight: 800, color: '#3D3022' }}>ریتاچر</span>
        </Link>

        {/* Desktop Links */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="hidden-mobile">
          {[
            { href: '/#services', label: 'خدمات' },
            { href: '/#how', label: 'نحوه کار' },
            { href: '/#editors', label: 'ادیتورها' },
            { href: '/#pricing', label: 'قیمت‌ها' },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              style={{ fontSize: 14, fontWeight: 500, color: '#5C5C5C', textDecoration: 'none' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#5C4A32')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#5C5C5C')}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {isAuthenticated && user ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setDropOpen(!dropOpen)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 14px', borderRadius: 10,
                  border: '1.5px solid #EDE5D8',
                  background: 'white', cursor: 'pointer',
                  fontSize: 13, fontWeight: 600, color: '#3D3022',
                  fontFamily: 'inherit',
                }}
              >
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: '#5C4A32', color: 'white',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700,
                }}>
                  {user.first_name?.[0] || user.username[0]}
                </div>
                {user.first_name || user.username}
              </button>

              {dropOpen && (
                <div style={{
                  position: 'absolute', top: '110%', left: 0,
                  background: 'white', borderRadius: 12,
                  border: '1px solid #EDE5D8',
                  boxShadow: '0 8px 24px rgba(0,0,0,.1)',
                  minWidth: 180, padding: '8px 0',
                  zIndex: 200,
                }}>
                  <Link href="/dashboard" style={dropItemStyle} onClick={() => setDropOpen(false)}>
                    <LayoutDashboard size={15} /> داشبورد
                  </Link>
                  <Link href="/dashboard/profile" style={dropItemStyle} onClick={() => setDropOpen(false)}>
                    <User size={15} /> پروفایل
                  </Link>
                  <hr style={{ margin: '6px 12px', borderColor: '#EDE5D8' }} />
                  <button
                    style={{ ...dropItemStyle, width: '100%', textAlign: 'right', background: 'none', border: 'none', cursor: 'pointer', color: '#E07070' }}
                    onClick={() => { clearAuth(); setDropOpen(false); }}
                  >
                    <LogOut size={15} /> خروج
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link href="/login" style={{
                padding: '8px 18px', borderRadius: 8,
                border: '1.5px solid #EDE5D8', background: 'transparent',
                fontSize: 13, fontWeight: 600, color: '#5C4A32', textDecoration: 'none',
              }}>
                ورود
              </Link>
              <Link href="/register" style={{
                padding: '8px 18px', borderRadius: 8,
                background: '#3D3022', color: 'white',
                fontSize: 13, fontWeight: 600, textDecoration: 'none',
                transition: 'background .2s',
              }}>
                شروع رایگان ↗
              </Link>
            </>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="show-mobile"
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#3D3022' }}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div style={{
          padding: '1rem 1.5rem 1.5rem',
          borderTop: '1px solid #EDE5D8',
          display: 'flex', flexDirection: 'column', gap: 12,
          background: 'white',
        }}>
          {[
            { href: '/#services', label: 'خدمات' },
            { href: '/#how', label: 'نحوه کار' },
            { href: '/#editors', label: 'ادیتورها' },
            { href: '/#pricing', label: 'قیمت‌ها' },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              style={{ fontSize: 15, color: '#5C5C5C', textDecoration: 'none', padding: '6px 0' }}
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}

const dropItemStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 8,
  padding: '9px 16px', fontSize: 13, fontWeight: 500,
  color: '#3D3022', textDecoration: 'none',
  transition: 'background .15s',
};