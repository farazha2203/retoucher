import Link from 'next/link';

export function Footer() {
  return (
    <footer style={{ background: '#3D3022', color: 'rgba(255,255,255,.7)', padding: '4rem 1.5rem 2rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: '3rem', marginBottom: '3rem' }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'white', marginBottom: '.75rem' }}>✦ ریتاچر</div>
            <p style={{ fontSize: 13, lineHeight: 1.9 }}>مارکت‌پلیس تخصصی روتوش، ادیت عکس و خدمات هوش مصنوعی تصویری در ایران.</p>
            <p style={{ fontSize: 12, marginTop: '.5rem', color: 'rgba(255,255,255,.4)' }}>هر تصویر، یک داستان می‌گوید.</p>
          </div>
          {[
            {
              title: 'خدمات',
              links: ['روتوش عکس', 'ادیت رنگ', 'هوش مصنوعی', 'آتلیه', 'ویدئو'],
            },
            {
              title: 'شرکت',
              links: ['درباره ما', 'وبلاگ', 'کارفرماها', 'ادیتورها', 'تماس'],
            },
            {
              title: 'پشتیبانی',
              links: ['مرکز راهنما', 'شرایط استفاده', 'حریم خصوصی', 'گزارش تخلف'],
            },
          ].map((col) => (
            <div key={col.title}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'white', marginBottom: '1rem' }}>{col.title}</div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
                {col.links.map((link) => (
                  <li key={link}>
                    <Link
                      href="/"
                      style={{ color: 'rgba(255,255,255,.6)', fontSize: 13, textDecoration: 'none' }}
                    >
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div style={{
          borderTop: '1px solid rgba(255,255,255,.1)',
          paddingTop: '1.5rem',
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', flexWrap: 'wrap', gap: '1rem',
        }}>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,.4)' }}>
            © {new Date().getFullYear()} ریتاچر. تمامی حقوق محفوظ است.
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            {['📷', '💬', '🐦'].map((icon) => (
              <div key={icon} style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'rgba(255,255,255,.1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', fontSize: 14,
              }}>{icon}</div>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}