import type { Metadata } from 'next';
import { Providers } from './providers';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'ریتاچر | مارکت‌پلیس تخصصی روتوش و ادیت عکس',
    template: '%s | ریتاچر',
  },
  description:
    'مارکت‌پلیس تخصصی ثبت و مدیریت سفارش‌های روتوش و ادیت عکس با انتخاب ادیتور، بازبینی و پرداخت امن.',
  keywords: [
    'روتوش عکس',
    'ادیت عکس',
    'فتوشاپ',
    'لایت‌روم',
    'مارکت‌پلیس ادیتور',
    'خدمات تصویری',
    'هوش مصنوعی تصویری',
    'آتلیه',
    'روتوشر',
    'ریتاچر',
  ],
  authors: [{ name: 'ریتاچر', url: 'https://retoucher.ir' }],
  creator: 'ریتاچر',
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'
  ),
  openGraph: {
    title: 'ریتاچر | مارکت‌پلیس تخصصی روتوش و ادیت عکس',
    description: 'فرایند شفاف ثبت سفارش، انتخاب ادیتور و تحویل پروژه',
    type: 'website',
    locale: 'fa_IR',
    siteName: 'ریتاچر',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ریتاچر',
    description: 'مارکت‌پلیس تخصصی روتوش و ادیت عکس',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
    },
  },
  alternates: { canonical: '/' },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
