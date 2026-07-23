'use client';

import { Building2, Megaphone, ShieldCheck, Upload } from 'lucide-react';

export default function StudioPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[34px] bg-gradient-to-l from-[#f8dfe9] via-[#eee7fb] to-[#def2e8] p-8">
        <Building2 className="text-[#7d68a0]"/>
        <h1 className="mt-4 text-3xl font-black text-[#40354b]">آتلیه و تبلیغات</h1>
        <p className="mt-3 text-sm text-[#7e7386]">
          لوگو، مشخصات عمومی، جایگاه تبلیغاتی و وضعیت تأیید آتلیه را مدیریت کن.
        </p>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        {[
          ['هویت تأییدشده','مدارک و مشخصات آتلیه',ShieldCheck],
          ['تبلیغات VIP','جایگاه ویژه در سایت',Megaphone],
          ['لوگو و گالری','هویت بصری آتلیه',Upload],
        ].map(([title,description,Icon]: any) => (
          <article key={title} className="rounded-[28px] border border-white bg-white/70 p-6 shadow-sm">
            <Icon className="text-[#8f74b8]"/>
            <strong className="mt-4 block text-[#473d50]">{title}</strong>
            <p className="mt-2 text-xs leading-6 text-[#8a7f91]">{description}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
