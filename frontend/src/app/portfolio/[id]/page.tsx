'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Flag,
  Heart,
  Loader2,
  MessageCircle,
  Send,
} from 'lucide-react';

import { portfolioAPI } from '@/lib/api/portfolio';
import type { PortfolioSocialItem } from '@/lib/types/portfolio';

export default function PortfolioSocialPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [item, setItem] = useState<PortfolioSocialItem | null>(null);
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState('');

  const load = async () => {
    const data = await portfolioAPI.get(id);
    setItem(data);
  };

  useEffect(() => {
    void load()
      .catch(() => setMessage('دریافت نمونه‌کار ناموفق بود.'))
      .finally(() => setLoading(false));
  }, [id]);

  const toggleLike = async () => {
    if (!item || working) return;
    setWorking(true);
    try {
      const result = await portfolioAPI.toggleLike(id);
      setItem({
        ...item,
        is_liked: result.liked,
        likes_count: result.likes_count,
      });
    } catch {
      setMessage('برای لایک باید وارد حساب شوید.');
    } finally {
      setWorking(false);
    }
  };

  const submitComment = async () => {
    if (!body.trim() || working) return;
    setWorking(true);
    try {
      await portfolioAPI.comment(id, body.trim());
      setBody('');
      setMessage('دیدگاه ثبت شد و پس از تأیید مدیر نمایش داده می‌شود.');
    } catch {
      setMessage('ثبت دیدگاه ناموفق بود.');
    } finally {
      setWorking(false);
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <Loader2 className="animate-spin text-violet-600" />
      </main>
    );
  }

  if (!item) {
    return <main className="p-8 text-center">نمونه‌کار پیدا نشد.</main>;
  }

  return (
    <main dir="rtl" className="min-h-screen bg-[#f8f6fb] px-4 py-8">
      <div className="mx-auto max-w-6xl">
        <Link href={`/editors/${item.editor_id}`} className="text-sm font-bold text-violet-700">
          بازگشت به پروفایل ادیتور
        </Link>

        <section className="mt-5 overflow-hidden rounded-[32px] border border-[#ebe5ef] bg-white shadow-xl shadow-purple-100/40">
          <div className="grid md:grid-cols-2">
            <ImagePane src={item.before_image} label="قبل" />
            <ImagePane src={item.after_image} label="بعد" />
          </div>

          <div className="p-6 sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <span className="text-xs font-bold text-violet-600">
                  {item.style_title || 'نمونه‌کار'}
                </span>
                <h1 className="mt-2 text-2xl font-black text-[#382f40]">
                  {item.title}
                </h1>
                <p className="mt-2 text-sm text-[#82778a]">
                  ادیتور: {item.editor_name}
                </p>
              </div>

              <button
                onClick={toggleLike}
                disabled={working}
                className={`flex items-center gap-2 rounded-2xl px-5 py-3 text-sm font-black ${
                  item.is_liked
                    ? 'bg-rose-100 text-rose-600'
                    : 'bg-[#f3eef9] text-[#765f91]'
                }`}
              >
                <Heart size={19} className={item.is_liked ? 'fill-current' : ''} />
                {item.likes_count}
              </button>
            </div>

            {item.description && (
              <p className="mt-5 text-sm leading-8 text-[#6f6577]">
                {item.description}
              </p>
            )}
          </div>
        </section>

        <section className="mt-6 rounded-[30px] border border-[#ebe5ef] bg-white p-6">
          <div className="flex items-center gap-2">
            <MessageCircle className="text-violet-600" />
            <h2 className="text-lg font-black">دیدگاه‌ها</h2>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-xs text-violet-700">
              {item.comments_count}
            </span>
          </div>

          <div className="mt-5 flex gap-3">
            <textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              rows={3}
              placeholder="نظر خودت را درباره این نمونه‌کار بنویس..."
              className="flex-1 rounded-2xl border border-[#e9e2ed] bg-[#fbfafc] p-4 text-sm outline-none focus:border-violet-400"
            />
            <button
              onClick={submitComment}
              disabled={working || body.trim().length < 2}
              className="self-end rounded-2xl bg-violet-600 p-4 text-white disabled:opacity-40"
            >
              <Send size={19} />
            </button>
          </div>

          {message && (
            <p className="mt-3 rounded-xl bg-[#f4eff9] p-3 text-xs text-[#765f91]">
              {message}
            </p>
          )}

          <div className="mt-6 space-y-4">
            {item.comments.map((comment) => (
              <article key={comment.id} className="rounded-2xl bg-[#faf8fc] p-4">
                <div className="flex justify-between gap-3">
                  <div>
                    <strong className="text-sm">{comment.username}</strong>
                    <p className="mt-2 text-sm leading-7 text-[#6e6475]">
                      {comment.body}
                    </p>
                  </div>
                  <button
                    title="گزارش دیدگاه"
                    onClick={() => {
                      const reason = window.prompt('علت گزارش را بنویسید');
                      if (reason) void portfolioAPI.reportComment(id, comment.id, reason);
                    }}
                    className="text-[#aaa1b0] hover:text-rose-500"
                  >
                    <Flag size={16} />
                  </button>
                </div>
                {comment.replies.map((reply) => (
                  <div key={reply.id} className="mr-6 mt-3 rounded-xl border-r-2 border-violet-200 bg-white p-3">
                    <strong className="text-xs">{reply.username}</strong>
                    <p className="mt-1 text-xs leading-6 text-[#756b7c]">
                      {reply.body}
                    </p>
                  </div>
                ))}
              </article>
            ))}

            {item.comments.length === 0 && (
              <div className="rounded-2xl border border-dashed border-[#ddd4e3] p-8 text-center text-sm text-[#918799]">
                هنوز دیدگاهی تأیید نشده است.
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function ImagePane({
  src,
  label,
}: {
  src: string | null;
  label: string;
}) {
  return (
    <div className="relative min-h-[320px] bg-[#eeeaf2]">
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt={label} className="h-full min-h-[320px] w-full object-cover" />
      ) : (
        <div className="flex min-h-[320px] items-center justify-center text-sm text-[#9b92a1]">
          تصویر موجود نیست
        </div>
      )}
      <span className="absolute right-4 top-4 rounded-full bg-black/65 px-3 py-1 text-xs font-bold text-white">
        {label}
      </span>
    </div>
  );
}
