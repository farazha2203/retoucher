import { Clock3 } from 'lucide-react';

import { WorkflowProgress } from '@/components/workflow/WorkflowProgress';
import type { WorkflowSummary } from '@/lib/types/workflow';

interface EntityCardProps {
  title: string;
  subtitle: string;
  workflow: WorkflowSummary;
  onTimeline: () => void;
}

export function EntityCard({
  title,
  subtitle,
  workflow,
  onTimeline,
}: EntityCardProps) {
  return (
    <article className="rounded-3xl border border-[#E5DDD2] bg-white p-5 shadow-sm">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="font-black text-[#332A23]">{title}</h3>
          <p className="mt-1 text-xs text-[#8A7E72]">{subtitle}</p>
        </div>
        <span className="rounded-full bg-[#F0EBE4] px-3 py-1 text-[11px] font-bold text-[#5D5147]">
          {workflow.status}
        </span>
      </div>

      <WorkflowProgress workflow={workflow} />

      <button
        type="button"
        onClick={onTimeline}
        className="mt-5 inline-flex items-center gap-2 rounded-xl border border-[#DDD3C7] px-3 py-2 text-xs font-bold text-[#54493F] hover:bg-[#F7F4EF]"
      >
        <Clock3 size={15} />
        مشاهده Timeline
      </button>
    </article>
  );
}
