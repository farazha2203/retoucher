import type { WorkflowSummary } from '@/lib/types/workflow';

function deadlineText(workflow: WorkflowSummary): string {
  const deadline = workflow.deadline;
  if (!deadline?.at) return 'بدون ضرب‌الاجل فعال';

  const date = new Intl.DateTimeFormat('fa-IR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(deadline.at));

  if (deadline.is_overdue) return `گذشته از موعد: ${date}`;
  return `مهلت: ${date}`;
}

export function WorkflowProgress({
  workflow,
}: {
  workflow: WorkflowSummary;
}) {
  const percent = Math.max(0, Math.min(100, workflow.progress_percent || 0));

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-xs font-bold text-[#5C5148]">
          {workflow.stage?.title_fa || workflow.status}
        </span>
        <span className="text-xs font-black text-[#352B23]">{percent}٪</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[#ECE5DC]">
        <div
          className={`h-full rounded-full transition-all ${
            workflow.deadline?.is_overdue ? 'bg-[#B65454]' : 'bg-[#52765D]'
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#887C70]">
        <span>{deadlineText(workflow)}</span>
        {workflow.waiting_for_role && (
          <span>منتظر: {workflow.waiting_for_role}</span>
        )}
      </div>
    </div>
  );
}
