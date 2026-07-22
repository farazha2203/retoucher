import type {
  WorkflowSummary,
  WorkflowTimelineEvent,
} from '@/types';

interface OrderWorkflowPanelProps {
  workflow?: WorkflowSummary;
  events: WorkflowTimelineEvent[];
}

const roleLabels: Record<string, string> = {
  client: 'کارفرما',
  editor: 'ادیتور',
  support: 'پشتیبانی',
  supervisor: 'ناظر',
  admin: 'مدیر',
};

const actionLabels: Record<string, string> = {
  submit: 'ارسال سفارش',
  review: 'بررسی سفارش',
  assign_editor: 'اختصاص ادیتور',
  start_editing: 'شروع ویرایش',
  upload_delivery: 'بارگذاری خروجی',
  supervisor_review: 'بررسی ناظر',
  client_review: 'بررسی کارفرما',
  approve: 'تأیید تحویل',
  request_revision: 'درخواست اصلاح',
  rate: 'ثبت امتیاز',
  settle: 'تسویه',
  close: 'بستن سفارش',
};

function formatDate(value?: string | null) {
  if (!value) return 'بدون مهلت فعال';

  try {
    return new Intl.DateTimeFormat('fa-IR', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function roleLabel(role?: string | null) {
  if (!role) return 'بدون اقدام در انتظار';
  return roleLabels[role] || role;
}

function actionLabel(action?: string | null) {
  if (!action) return 'اقدام بعدی مشخص نشده';
  return actionLabels[action] || action.replaceAll('_', ' ');
}

export function OrderWorkflowPanel({
  workflow,
  events,
}: OrderWorkflowPanelProps) {
  if (!workflow) {
    return (
      <section className="rounded-3xl border border-dashed border-[#D8CEC2] bg-white p-6 text-sm text-[#81766C]">
        اطلاعات گردش‌کار برای این سفارش هنوز در پاسخ Backend موجود نیست.
      </section>
    );
  }

  const progress = Math.max(
    0,
    Math.min(100, workflow.progress_percent || 0),
  );

  return (
    <section className="overflow-hidden rounded-3xl border border-[#E6DED5] bg-white shadow-sm">
      <div className="border-b border-[#EEE7DF] p-6 sm:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-bold text-[#8B7E72]">گردش‌کار سفارش</p>
            <h2 className="mt-1 text-xl font-black text-[#352C25]">
              {workflow.stage?.title_fa || workflow.status}
            </h2>
          </div>

          <div className="grid gap-2 text-xs sm:grid-cols-2">
            <WorkflowBadge
              label="مسئول اقدام"
              value={roleLabel(workflow.waiting_for_role)}
            />
            <WorkflowBadge
              label="اقدام بعدی"
              value={actionLabel(workflow.next_action)}
            />
          </div>
        </div>

        <div className="mt-6">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-bold text-[#6D6258]">
              پیشرفت سفارش
            </span>
            <span className="text-sm font-black text-[#352C25]">
              {progress}٪
            </span>
          </div>

          <div
            className="h-3 overflow-hidden rounded-full bg-[#EEE8E1]"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                workflow.deadline?.is_overdue
                  ? 'bg-[#B65454]'
                  : workflow.successful
                    ? 'bg-[#4F785B]'
                    : 'bg-[#806B57]'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div
          className={`mt-5 rounded-2xl p-4 text-sm ${
            workflow.deadline?.is_overdue
              ? 'border border-[#E7BABA] bg-[#FFF4F4] text-[#984747]'
              : 'border border-[#E6DED5] bg-[#FAF8F5] text-[#655A50]'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="font-bold">
              {workflow.deadline?.is_overdue
                ? 'مهلت این مرحله گذشته است'
                : 'مهلت مرحله فعلی'}
            </span>
            <time>{formatDate(workflow.deadline?.at)}</time>
          </div>

          {workflow.deadline?.timeout_action && (
            <p className="mt-2 text-xs opacity-75">
              اقدام Backend پس از پایان مهلت:{' '}
              {actionLabel(workflow.deadline.timeout_action)}
            </p>
          )}
        </div>
      </div>

      <div className="p-6 sm:p-8">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-[#8B7E72]">Timeline</p>
            <h3 className="mt-1 text-lg font-black text-[#352C25]">
              تاریخچه سفارش
            </h3>
          </div>
          <span className="rounded-full bg-[#F1ECE6] px-3 py-1 text-xs font-bold text-[#62564B]">
            {events.length} رویداد
          </span>
        </div>

        {events.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-[#D8CEC2] p-5 text-center text-sm text-[#887C71]">
            هنوز رویدادی در Timeline ثبت نشده است.
          </p>
        ) : (
          <ol className="relative space-y-5 before:absolute before:bottom-2 before:right-[7px] before:top-2 before:w-px before:bg-[#DED5CB]">
            {events.map((event) => (
              <li key={event.event_id} className="relative pr-8">
                <span className="absolute right-0 top-1.5 h-4 w-4 rounded-full border-4 border-white bg-[#806B57] shadow-sm" />

                <article className="rounded-2xl border border-[#EBE4DC] bg-[#FCFBF9] p-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <p className="text-sm font-bold leading-7 text-[#40362E]">
                      {event.message || event.event_key}
                    </p>
                    <time className="shrink-0 text-[11px] text-[#94887D]">
                      {formatDate(event.occurred_at)}
                    </time>
                  </div>

                  {(event.from_status || event.to_status) && (
                    <p className="mt-2 text-xs text-[#7D7166]">
                      {event.from_status || '—'} ← {event.to_status || '—'}
                    </p>
                  )}

                  <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[#968A7F]">
                    {event.actor?.username && (
                      <span>توسط {event.actor.username}</span>
                    )}
                    {event.source && <span>منبع: {event.source}</span>}
                  </div>
                </article>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}

function WorkflowBadge({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl bg-[#F5F1EC] px-4 py-3">
      <p className="text-[10px] text-[#95887C]">{label}</p>
      <p className="mt-1 font-bold text-[#4C4138]">{value}</p>
    </div>
  );
}
