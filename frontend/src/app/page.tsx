import type { Metadata } from 'next';
import LandingPageClient from '@/components/LandingPageClient';

export const metadata: Metadata = {
  title: 'ریتاچر | مارکت‌پلیس تخصصی روتوش و ادیت عکس',
  description:
    'ثبت و مدیریت سفارش‌های روتوش و ادیت عکس با فرایند شفاف انتخاب ادیتور، بازبینی و پرداخت امن.',
};

export default function Page() {
  return <LandingPageClient />;
}
