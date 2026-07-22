import { Suspense } from 'react';
import NewOrderClient from './NewOrderClient';

export default function NewOrderPage() {
  return (
    <Suspense
      fallback={
        <main
          className="min-h-screen px-4 py-10"
          style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
        >
          <div className="mx-auto max-w-3xl">
            <section className="rounded-3xl bg-white p-8 text-center shadow-sm">
              <p className="text-sm text-gray-500">در حال آماده‌سازی فرم سفارش...</p>
            </section>
          </div>
        </main>
      }
    >
      <NewOrderClient />
    </Suspense>
  );
}