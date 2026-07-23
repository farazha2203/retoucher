import { Suspense } from 'react';

import { AuthCallbackClient } from './AuthCallbackClient';

function CallbackFallback() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <section className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl">
        <div className="mx-auto mb-5 h-16 w-16 animate-pulse rounded-2xl bg-violet-100" />
        <h1 className="text-xl font-bold text-slate-900">ورود به ریتاچر</h1>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          در حال آماده‌سازی ورود امن...
        </p>
      </section>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<CallbackFallback />}>
      <AuthCallbackClient />
    </Suspense>
  );
}
