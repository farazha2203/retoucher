import type { ReactNode } from 'react';
import '../../styles/auth.css';

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen" style={{ fontFamily: 'var(--font-vazirmatn), system-ui' }}>
      {children}
    </div>
  );
}