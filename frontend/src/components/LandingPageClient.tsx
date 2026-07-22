'use client';

import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

export default function LandingPageClient() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <TrustBar />
        <ServicesSection />
        <HowItWorks />
        <EditorTypesSection />
        <PricingSection />
        <TestimonialsSection />
        <CTASection />
      </main>
      <Footer />
    </>
  );
}

// ─── Hero ───────────────────────────────────────────
function HeroSection() {
  return (
    <section
      id="hero"
      style={{
        background: 'linear-gradient(160deg,#F9F5EF 0%,#EBF4EE 50%,#E8EFF8 100%)',
        padding: 'clamp(4rem,8vw,7rem) 1.5rem 4rem',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'rgba(92,74,50,.05)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: -80,
          left: -80,
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: 'rgba(45,90,61,.05)',
          pointerEvents: 'none',
        }}
      />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 800, margin: '0 auto' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 16px',
            borderRadius: 20,
            background: '#EBF4EE',
            border: '1px solid rgba(45,90,61,.2)',
            fontSize: 12,
            fontWeight: 700,
            color: '#2D5A3D',
            marginBottom: '1.5rem',
          }}
        >
          شبکه تخصصی ادیتورهای حرفه‌ای
        </div>

        <h1
          style={{
            fontSize: 'clamp(28px,5vw,56px)',
            fontWeight: 900,
            lineHeight: 1.2,
            color: '#3D3022',
            marginBottom: '.8rem',
          }}
        >
          بهترین ادیتورها را <span style={{ color: '#2D5A3D' }}>در یک کلیک</span> پیدا کنید
        </h1>

        <p
          style={{
            fontSize: 'clamp(14px,2vw,18px)',
            color: '#5C5C5C',
            lineHeight: 1.8,
            maxWidth: 550,
            margin: '0 auto 2.5rem',
          }}
        >
          ریتاچر، مارکت‌پلیس تخصصی روتوش، ادیت عکس، آتلیه و هوش مصنوعی تصویری.
          کارفرما سفارش بده، ادیتور کار کن، هر دو رشد کنید.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link
            href="/register"
            style={{
              padding: '14px 36px',
              borderRadius: 12,
              background: '#3D3022',
              color: 'white',
              fontSize: 15,
              fontWeight: 700,
              textDecoration: 'none',
              display: 'inline-block',
              boxShadow: '0 4px 16px rgba(92,74,50,.25)',
            }}
          >
            ثبت سفارش رایگان
          </Link>
          <Link
            href="#how"
            style={{
              padding: '14px 36px',
              borderRadius: 12,
              border: '2px solid #2D5A3D',
              color: '#1A3D28',
              fontSize: 15,
              fontWeight: 700,
              textDecoration: 'none',
              display: 'inline-block',
            }}
          >
            ببین چطور کار می‌کند ▶
          </Link>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '3rem',
            marginTop: '4rem',
            flexWrap: 'wrap',
          }}
        >
          {[
            { num: 'شفاف', label: 'گردش کار پروژه' },
            { num: 'کنترل‌شده', label: 'بازبینی و اصلاح' },
            { num: 'امن', label: 'پرداخت و تسویه' },
            { num: 'قابل پیگیری', label: 'وضعیت سفارش' },
          ].map((s) => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 900, color: '#3D3022' }}>{s.num}</div>
              <div style={{ fontSize: 12, color: '#5C5C5C', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrustBar() {
  return (
    <div style={{ background: '#3D3022', padding: '1rem 1.5rem' }}>
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '3rem',
          flexWrap: 'wrap',
        }}
      >
        {[
          { icon: '🔒', label: 'پرداخت امن' },
          { icon: '✅', label: 'ادیتورهای تایید شده' },
          { icon: '⚖️', label: 'فرآیند حل اختلاف' },
          { icon: '⚡', label: 'تحویل سریع' },
          { icon: '🤝', label: 'پشتیبانی مرحله‌ای' },
        ].map((item) => (
          <div
            key={item.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: 'rgba(255,255,255,.8)',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            <span style={{ fontSize: 18 }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}

function ServicesSection() {
  const services = [
    {
      icon: '🎨',
      title: 'روتوش عکس',
      desc: 'روتوش حرفه‌ای پرتره، مد، تبلیغات و محصول.',
      tags: ['پرتره', 'مد', 'محصول'],
      accent: '#5C4A32',
    },
    {
      icon: '📸',
      title: 'ادیت و رنگ‌بندی',
      desc: 'Color grading حرفه‌ای، تنظیم نور و رنگ.',
      tags: ['Color Grade', 'LUT', 'Preset'],
      accent: '#2D5A3D',
    },
    {
      icon: '🤖',
      title: 'هوش مصنوعی',
      desc: 'تولید تصویر با AI، Inpainting، Upscaling.',
      tags: ['Midjourney', 'Stable Diffusion', 'AI Fix'],
      accent: '#1E3A5F',
    },
    {
      icon: '🏢',
      title: 'خدمات آتلیه',
      desc: 'ویرایش دسته‌ای عکس‌های آتلیه، تغییر بک‌گراند.',
      tags: ['کودک', 'عروسی', 'تجاری'],
      accent: '#5C4A32',
    },
    {
      icon: '🛍️',
      title: 'عکاسی محصول',
      desc: 'حذف پس‌زمینه، Ghost Mannequin، آماده‌سازی E-commerce.',
      tags: ['بک‌گراند سفید', 'Ghost'],
      accent: '#2D5A3D',
    },
    {
      icon: '🎬',
      title: 'ویدئو و موشن',
      desc: 'ادیت ویدئو، Color Grade، ساخت کلیپ تبلیغاتی.',
      tags: ['Reels', 'TikTok', 'تجاری'],
      accent: '#1E3A5F',
    },
  ];

  return (
    <section id="services" style={{ padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader
          eyebrow="خدمات ما"
          title="هر نوع خدمات تصویری که نیاز دارید"
          desc="از روتوش ساده تا پروژه‌های سنگین تجاری — ادیتورهای تخصصی ما آماده‌اند"
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
            gap: '1.5rem',
          }}
        >
          {services.map((s) => (
            <div
              key={s.title}
              style={{
                background: 'white',
                borderRadius: 16,
                border: '1px solid #EDE5D8',
                padding: '2rem',
                transition: 'all .3s',
                borderRight: `4px solid ${s.accent}`,
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 16px 40px rgba(0,0,0,.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = '';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  background: s.accent + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                  marginBottom: '1.25rem',
                }}
              >
                {s.icon}
              </div>
              <h3
                style={{
                  fontSize: 17,
                  fontWeight: 700,
                  color: '#3D3022',
                  marginBottom: '.5rem',
                }}
              >
                {s.title}
              </h3>
              <p style={{ fontSize: 13, color: '#5C5C5C', lineHeight: 1.8 }}>{s.desc}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: '1rem' }}>
                {s.tags.map((t) => (
                  <span
                    key={t}
                    style={{
                      padding: '3px 10px',
                      borderRadius: 20,
                      fontSize: 11,
                      fontWeight: 600,
                      background: s.accent + '12',
                      color: s.accent,
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { n: '۱', title: 'سفارش ثبت کنید', desc: 'پروژه خود را با جزئیات توضیح دهید — نوع کار، بودجه، و زمان‌بندی' },
    { n: '۲', title: 'ادیتور انتخاب کنید', desc: 'پیشنهادات ادیتورها را مقایسه کنید و بهترین گزینه را انتخاب کنید' },
    { n: '۳', title: 'کار انجام می‌شود', desc: 'ادیتور در ضرب‌الاجل مشخص کار را تحویل می‌دهد' },
    { n: '۴', title: 'تایید و پرداخت', desc: 'پس از تایید نهایی، وجه به ادیتور پرداخت می‌شود' },
  ];

  return (
    <section id="how" style={{ background: '#F9F5EF', padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader
          eyebrow="نحوه کار"
          title="در ۴ گام ساده شروع کنید"
          desc="از ثبت سفارش تا تحویل نهایی — فرایند شفاف و مطمئن"
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))',
            gap: '1.5rem',
          }}
        >
          {steps.map((s) => (
            <div key={s.n} style={{ textAlign: 'center', padding: '2rem 1.5rem' }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: '#3D3022',
                  color: 'white',
                  fontSize: 18,
                  fontWeight: 900,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 1.25rem',
                }}
              >
                {s.n}
              </div>
              <h3
                style={{
                  fontSize: 16,
                  fontWeight: 700,
                  color: '#3D3022',
                  marginBottom: '.5rem',
                }}
              >
                {s.title}
              </h3>
              <p style={{ fontSize: 13, color: '#5C5C5C', lineHeight: 1.8 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EditorTypesSection() {
  const types = [
    { emoji: '👤', title: 'روتوشر پرتره', desc: 'ویرایش عکس‌های چهره و پوست', count: '+۱۲۰ ادیتور' },
    { emoji: '👗', title: 'ادیتور مد', desc: 'کار با برندهای لباس و اکسسوری', count: '+۸۰ ادیتور' },
    { emoji: '🏠', title: 'معماری', desc: 'ادیت فضای داخلی و دکوراسیون', count: '+۴۵ ادیتور' },
    { emoji: '💒', title: 'عکاسی عروسی', desc: 'ادیت آلبوم عروس و داماد', count: '+۹۰ ادیتور' },
    { emoji: '🍔', title: 'عکاسی غذا', desc: 'ویرایش تصاویر رستوران و کافه', count: '+۳۵ ادیتور' },
  ];

  return (
    <section id="editors" style={{ padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader eyebrow="تخصص‌ها" title="ادیتورهای تخصصی در هر حوزه‌ای" />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))',
            gap: '1rem',
          }}
        >
          {types.map((t) => (
            <div
              key={t.title}
              style={{
                background: 'white',
                border: '1px solid #EDE5D8',
                borderRadius: 14,
                padding: '1.75rem 1.5rem',
                textAlign: 'center',
                transition: 'all .25s',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#2D5A3D';
                e.currentTarget.style.background = '#EBF4EE';
                e.currentTarget.style.transform = 'translateY(-3px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#EDE5D8';
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.transform = '';
              }}
            >
              <span style={{ fontSize: 36, display: 'block', marginBottom: '.75rem' }}>{t.emoji}</span>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#3D3022', marginBottom: '.4rem' }}>
                {t.title}
              </div>
              <div style={{ fontSize: 12, color: '#5C5C5C', lineHeight: 1.7 }}>{t.desc}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#2D5A3D', marginTop: '.75rem' }}>
                {t.count}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PricingSection() {
  const plans = [
    {
      name: 'کارفرما رایگان',
      price: 'رایگان',
      sub: 'برای همیشه',
      desc: 'برای کسی که می‌خواهد سفارش ثبت کند',
      features: ['ثبت نامحدود پروژه', 'دسترسی به تمام ادیتورها', 'سیستم اسکرو امن', 'پشتیبانی چت'],
      cta: 'شروع کنید',
      featured: false,
    },
    {
      name: 'ادیتور حرفه‌ای',
      price: '۱۰٪',
      sub: 'کمیسیون از درآمد',
      desc: 'برای ادیتورهایی که خدمات ارائه می‌دهند',
      features: ['پروفایل حرفه‌ای', 'نمایش پرتفولیو', 'دریافت پیشنهاد پروژه', 'کیف پول و برداشت', 'امتیازدهی'],
      cta: 'همین الان شروع کن',
      featured: true,
    },
    {
      name: 'آتلیه و استودیو',
      price: 'سفارشی',
      sub: 'تماس بگیرید',
      desc: 'برای تیم‌های بزرگ با حجم کاری بالا',
      features: ['داشبورد تیمی', 'مدیریت چند ادیتور', 'قرارداد سفارشی', 'کمیسیون ویژه'],
      cta: 'تماس با ما',
      featured: false,
    },
  ];

  return (
    <section
      id="pricing"
      style={{
        background: 'linear-gradient(160deg,#E8EFF8 0%,#F9F5EF 100%)',
        padding: '5rem 1.5rem',
      }}
    >
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <SectionHeader
          eyebrow="قیمت‌گذاری"
          title="شفاف، منصفانه، برای همه"
          desc="ریتاچر فقط ۱۰٪ کمیسیون می‌گیرد. بدون هزینه مخفی."
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))',
            gap: '1.5rem',
          }}
        >
          {plans.map((plan) => (
            <div
              key={plan.name}
              style={{
                background: 'white',
                borderRadius: 16,
                padding: '2.5rem 2rem',
                border: plan.featured ? '2px solid #3D3022' : '2px solid #EDE5D8',
                position: 'relative',
              }}
            >
              {plan.featured && (
                <div
                  style={{
                    position: 'absolute',
                    top: -14,
                    right: '50%',
                    transform: 'translateX(50%)',
                    background: '#3D3022',
                    color: 'white',
                    fontSize: 11,
                    fontWeight: 700,
                    padding: '4px 16px',
                    borderRadius: 20,
                    whiteSpace: 'nowrap',
                  }}
                >
                  محبوب‌ترین
                </div>
              )}
              <div style={{ fontSize: 14, fontWeight: 700, color: '#5C5C5C', marginBottom: '.5rem' }}>
                {plan.name}
              </div>
              <div style={{ fontSize: 32, fontWeight: 900, color: '#3D3022' }}>
                {plan.price}{' '}
                <span style={{ fontSize: 14, fontWeight: 500, color: '#5C5C5C' }}>{plan.sub}</span>
              </div>
              <p style={{ fontSize: 13, color: '#5C5C5C', margin: '.75rem 0 1.5rem', lineHeight: 1.7 }}>
                {plan.desc}
              </p>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {plan.features.map((f) => (
                  <li
                    key={f}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontSize: 13,
                      color: '#5C5C5C',
                      padding: '5px 0',
                      borderBottom: '1px solid #F9F5EF',
                    }}
                  >
                    <span style={{ color: '#2D5A3D', fontWeight: 700 }}>✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                style={{
                  display: 'block',
                  width: '100%',
                  padding: 12,
                  borderRadius: 10,
                  marginTop: '1.5rem',
                  textAlign: 'center',
                  fontSize: 14,
                  fontWeight: 700,
                  textDecoration: 'none',
                  ...(plan.featured
                    ? { background: '#3D3022', color: 'white' }
                    : { border: '2px solid #3D3022', color: '#3D3022', background: 'transparent' }),
                }}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TestimonialsSection() {
  const items = [
    {
      text: 'ریتاچر زندگیم رو تغییر داد. الان ماهانه ۱۵ میلیون درآمد دارم از همین پلتفرم.',
      name: 'امیر رضایی',
      role: 'روتوشر حرفه‌ای',
      color: '#2D5A3D',
      initial: 'ا',
    },
    {
      text: 'برای آتلیه‌ام عالیه. سیستم امن و پشتیبانی سریع.',
      name: 'نرگس محمدی',
      role: 'مدیر آتلیه',
      color: '#5C4A32',
      initial: 'ن',
    },
    {
      text: 'سیستم اسکرو خیلی مطمئنه. این اعتماد ایجاد می‌کنه برای هر دو طرف.',
      name: 'سینا کریمی',
      role: 'عکاس تجاری',
      color: '#1E3A5F',
      initial: 'س',
    },
  ];

  return (
    <section style={{ padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader eyebrow="نظرات کاربران" title="آنچه کاربران می‌گویند" />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
            gap: '1.5rem',
          }}
        >
          {items.map((item) => (
            <div
              key={item.name}
              style={{
                background: '#F9F5EF',
                borderRadius: 16,
                padding: '2rem',
                border: '1px solid #EDE5D8',
              }}
            >
              <div style={{ fontSize: 28, color: '#5C4A32', marginBottom: '1rem' }}>"</div>
              <p style={{ fontSize: 14, color: '#5C5C5C', lineHeight: 1.9, marginBottom: '1.5rem' }}>
                {item.text}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    background: item.color,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                  }}
                >
                  {item.initial}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#3D3022' }}>{item.name}</div>
                  <div style={{ fontSize: 12, color: '#9A9A9A' }}>{item.role}</div>
                  <div style={{ color: '#F0B429', fontSize: 13 }}>★★★★★</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section
      style={{
        background: 'linear-gradient(135deg,#3D3022 0%,#1A3D28 100%)',
        padding: '5rem 1.5rem',
        textAlign: 'center',
      }}
    >
      <h2
        style={{
          fontSize: 'clamp(22px,4vw,40px)',
          fontWeight: 900,
          color: 'white',
          marginBottom: '1rem',
        }}
      >
        آماده‌اید شروع کنید؟
      </h2>
      <p
        style={{
          fontSize: 15,
          color: 'rgba(255,255,255,.75)',
          maxWidth: 500,
          margin: '0 auto 2.5rem',
          lineHeight: 1.8,
        }}
      >
        به جمع هزاران کارفرما و ادیتور حرفه‌ای ریتاچر بپیوندید.
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link
          href="/register?role=client"
          style={{
            padding: '14px 32px',
            borderRadius: 12,
            background: 'white',
            color: '#3D3022',
            fontSize: 15,
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          کارفرما هستم — سفارش ثبت کنم
        </Link>
        <Link
          href="/register?role=editor"
          style={{
            padding: '14px 32px',
            borderRadius: 12,
            border: '2px solid rgba(255,255,255,.5)',
            color: 'white',
            fontSize: 15,
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          ادیتور هستم — پروفایل بسازم
        </Link>
      </div>
    </section>
  );
}

function SectionHeader({
  eyebrow,
  title,
  desc,
}: {
  eyebrow: string;
  title: string;
  desc?: string;
}) {
  return (
    <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
      <span
        style={{
          display: 'inline-block',
          fontSize: 12,
          fontWeight: 700,
          color: '#2D5A3D',
          textTransform: 'uppercase',
          letterSpacing: '.1em',
          marginBottom: '.75rem',
        }}
      >
        {eyebrow}
      </span>
      <h2
        style={{
          fontSize: 'clamp(22px,3.5vw,36px)',
          fontWeight: 900,
          color: '#3D3022',
          marginBottom: '.75rem',
        }}
      >
        {title}
      </h2>
      {desc && (
        <p style={{ fontSize: 15, color: '#5C5C5C', maxWidth: 500, margin: '0 auto', lineHeight: 1.8 }}>
          {desc}
        </p>
      )}
    </div>
  );
}