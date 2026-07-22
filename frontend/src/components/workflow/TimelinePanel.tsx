import { X } from 'lucide-react';

import type { TimelineResponse } from '@/lib/types/workflow';

interface TimelinePanelProps {
  open: boolean;
  title: string;
  loading: boolean;
  data?: TimelineResponse;
  onClose: () => void;
}

export function TimelinePanel({
  open,
  title,
  loading,
  data,
  onClose,
}: TimelinePanelProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70]">
      <button
        type="button"
        className="absolute inset-0 bg-black/35"
        onClick={onClose}
        aria-label="بستن Timeline"
      />
      <section className="absolute inset-y-0 left-0 w-full max-w-lg overflow-y-auto bg-white p-5 shadow-2xl sm:p-7">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs text-[#8B7F73]">تاریخچه روند</p>
            <h2 className="mt-1 text-lg font-black text-[#332A23]">{title}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-[#E5DDD2] p-2"
          >
            <X size={18} />
          </button>
        </div>

        {loading && <p className="text-sm text-[#7C7064]">در حال دریافت...</p>}

        {!loading && data?.events.length === 0 && (
          <p className="rounded-2xl bg-[#F7F4EF] p-5 text-sm text-[#7C7064]">
            هنوز رویدادی ثبت نشده است.
          </p>
        )}

        <div className="space-y-3">
          {data?.events.map((event) => (
            <article
              key={event.event_id}
              className="rounded-2xl border border-[#E9E1D8] p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm font-bold text-[#3C322A]">
                  {event.message || event.event_key}
                </p>
                <time className="shrink-0 text-[10px] text-[#94887C]">
                  {new Intl.DateTimeFormat('fa-IR', {
                    dateStyle: 'short',
                    timeStyle: 'short',
                  }).format(new Date(event.occurred_at))}
                </time>
              </div>
              {(event.from_status || event.to_status) && (
                <p className="mt-2 text-xs text-[#807469]">
                  {event.from_status || '—'} ← {event.to_status || '—'}
                </p>
              )}
              {event.actor && (
                <p className="mt-2 text-[11px] text-[#A0958A]">
                  توسط {event.actor.username}
                </p>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
