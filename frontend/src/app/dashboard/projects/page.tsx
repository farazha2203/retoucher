'use client';

import { EntityCard } from '@/components/workflow/EntityCard';
import { TimelinePanel } from '@/components/workflow/TimelinePanel';
import {
  useProjectRequests,
  useProjectTimeline,
} from '@/lib/hooks/useProjectRequests';
import { useState } from 'react';

export default function ProjectsPage() {
  const projects = useProjectRequests();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const timeline = useProjectTimeline(selectedId);
  const selected = projects.data?.find((item) => item.id === selectedId);

  return (
    <>
      <div className="mb-7">
        <h1 className="text-2xl font-black text-[#332A23]">درخواست‌های پروژه</h1>
        <p className="mt-2 text-sm text-[#82766A]">
          مشاهده روش سفارش، مرحله فعلی، درصد پیشرفت و Timeline
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {projects.data?.map((project) => (
          <EntityCard
            key={project.id}
            title={project.title}
            subtitle={project.request_type_display || project.request_type}
            workflow={project.workflow}
            onTimeline={() => setSelectedId(project.id)}
          />
        ))}
      </div>

      {!projects.isLoading && projects.data?.length === 0 && (
        <p className="rounded-3xl border border-dashed border-[#D9CEC0] bg-white p-8 text-center text-sm text-[#8A7E72]">
          درخواستی موجود نیست.
        </p>
      )}

      <TimelinePanel
        open={selectedId !== null}
        title={selected?.title || 'درخواست پروژه'}
        loading={timeline.isLoading}
        data={timeline.data}
        onClose={() => setSelectedId(null)}
      />
    </>
  );
}
