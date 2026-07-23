'use client';

import { useEffect, useState } from 'react';
import { ImagePlus, Pencil, Save, Send, Trash2 } from 'lucide-react';
import { editorWorkspaceAPI } from '@/lib/api/editor-workspace';
import type { EditorWorkspacePortfolioItem, EditorWorkspaceProfile } from '@/lib/types/editor-workspace';

const labels = { draft: 'پیش‌نویس', pending: 'در انتظار بررسی', approved: 'منتشرشده', rejected: 'ردشده' };

export default function EditorWorkspacePage() {
  const [profile, setProfile] = useState<EditorWorkspaceProfile | null>(null);
  const [editing, setEditing] = useState<EditorWorkspacePortfolioItem | null>(null);
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);

  const refresh = async () => setProfile(await editorWorkspaceAPI.getMe());
  useEffect(() => { void refresh().catch(() => setMessage('پروفایل دریافت نشد.')); }, []);

  if (!profile) return <div className="rounded-3xl bg-white p-8">{message || 'در حال دریافت...'}</div>;

  const saveProfile = async () => {
    setSaving(true);
    try { setProfile(await editorWorkspaceAPI.updateProfile(profile)); setMessage('پروفایل ذخیره شد.'); }
    catch { setMessage('ذخیره ناموفق بود.'); }
    finally { setSaving(false); }
  };

  const saveItem = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setSaving(true);
    try {
      const data = new FormData(event.currentTarget);
      if (editing) await editorWorkspaceAPI.updatePortfolio(editing.id, data);
      else await editorWorkspaceAPI.createPortfolio(data);
      setEditing(null); event.currentTarget.reset(); await refresh();
      setMessage('نمونه‌کار ذخیره شد.');
    } catch { setMessage('ذخیره نمونه‌کار ناموفق بود.'); }
    finally { setSaving(false); }
  };

  return <div className="space-y-6">
    <section className="rounded-[32px] bg-gradient-to-l from-[#35294b] to-[#725896] p-7 text-white"><h1 className="text-3xl font-black">{profile.display_name}</h1><p className="mt-2 text-white/65">مدیریت کامل پورتفولیو</p></section>
    {message && <div className="rounded-2xl bg-[#f2edf8] p-4 text-sm">{message}</div>}
    <section className="grid gap-6 xl:grid-cols-2">
      <div className="rounded-[30px] border bg-white p-6">
        <h2 className="text-lg font-black">پروفایل همکاری</h2>
        <input className="mt-5 w-full rounded-2xl border p-3" value={profile.display_name} onChange={(e)=>setProfile({...profile,display_name:e.target.value})}/>
        <textarea className="mt-3 w-full rounded-2xl border p-3" rows={5} value={profile.bio} onChange={(e)=>setProfile({...profile,bio:e.target.value})}/>
        <button onClick={saveProfile} disabled={saving} className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-violet-600 p-3 text-white"><Save size={17}/>ذخیره</button>
      </div>
      <form onSubmit={saveItem} className="rounded-[30px] border bg-white p-6">
        <h2 className="text-lg font-black">{editing ? 'ویرایش نمونه‌کار' : 'نمونه‌کار جدید'}</h2>
        <input name="title" defaultValue={editing?.title || ''} key={`t-${editing?.id || 0}`} className="mt-5 w-full rounded-2xl border p-3" placeholder="عنوان" required/>
        <textarea name="description" defaultValue={editing?.description || ''} key={`d-${editing?.id || 0}`} className="mt-3 w-full rounded-2xl border p-3" rows={4} placeholder="توضیح"/>
        <input name="before_image" type="file" accept="image/*" className="mt-3 w-full rounded-2xl border p-3"/>
        <input name="after_image" type="file" accept="image/*" className="mt-3 w-full rounded-2xl border p-3"/>
        <button disabled={saving} className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-l from-[#df79a0] to-[#9278db] p-3 text-white"><ImagePlus size={17}/>ذخیره پیش‌نویس</button>
      </form>
    </section>
    <section className="rounded-[30px] border bg-white p-6">
      <h2 className="text-lg font-black">نمونه‌کارهای من</h2>
      <div className="mt-5 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      {profile.portfolio_items.map((item)=><article key={item.id} className="rounded-3xl border p-4">
        <div className="flex justify-between gap-2"><strong>{item.title}</strong><span className="rounded-full bg-violet-50 px-2 py-1 text-[10px]">{labels[item.review_status]}</span></div>
        {item.review_note && <p className="mt-3 rounded-xl bg-amber-50 p-2 text-xs text-amber-700">{item.review_note}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          {item.review_status !== 'pending' && <button onClick={()=>setEditing(item)} className="flex items-center gap-1 rounded-xl bg-blue-50 px-3 py-2 text-xs"><Pencil size={14}/>ویرایش</button>}
          {['draft','rejected'].includes(item.review_status) && <button onClick={async()=>{await editorWorkspaceAPI.submitPortfolio(item.id);await refresh();}} className="flex items-center gap-1 rounded-xl bg-emerald-50 px-3 py-2 text-xs"><Send size={14}/>ارسال بررسی</button>}
          {item.review_status !== 'pending' && <button onClick={async()=>{if(confirm('حذف شود؟')){await editorWorkspaceAPI.deletePortfolio(item.id);await refresh();}}} className="flex items-center gap-1 rounded-xl bg-rose-50 px-3 py-2 text-xs"><Trash2 size={14}/>حذف</button>}
        </div>
      </article>)}
      </div>
    </section>
  </div>;
}
