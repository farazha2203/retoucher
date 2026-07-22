'use client';

import {
  AlertTriangle,
  BriefcaseBusiness,
  CheckCircle2,
  FolderKanban,
} from 'lucide-react';

import { EntityCard } from '@/components/workflow/EntityCard';
import { TimelinePanel } from '@/components/workflow/TimelinePanel';
import { useOrders, useOrderTimeline } from '@/lib/hooks/useOrders';
import {
  useProjectRequests,
  useProjectTimeline,
} from '@/lib/hooks/useProjectRequests';
import { useState } from 'react';

type SelectedEntity =
  | { type: 'order'; id: number; title: string }
  | { type: 'project'; id: number; title: string }
  | null;

export default function DashboardPage() {
  const orders = useOrders();
  const projects = useProjectRequests();
  const [selected, setSelected] = useState<SelectedEntity>(null);

  const orderTimeline = useOrderTimeline(
    selected?.type === 'order' ? selected.id : null,
  );
  const projectTimeline = useProjectTimeline(
    selected?.type === 'project' ? selected.id : null,
  );

  const orderList = orders.data || [];
  const projectList = projects.data || [];
  const allWorkflows = [
    ...orderList.map((item) => item.workflow),
    ...projectList.map((item) => item.workflow),
  ];

  const stats = [
    {
      title: 'سفارش‌ها',
      value: orderList.length,
      icon: BriefcaseBusiness,
    },
    {
      title: 'درخواست‌ها',
      value: projectList.length,
      icon: FolderKanban,
    },
    {
      title: 'در حال اجرا',
      value: allWorkflows.filter((item) => !item.terminal).length,
      icon: CheckCircle2,
    },
    {
      title: 'گذشته از موعد',
      value: allWorkflows.filter((item) => item.deadline?.is_overdue).length,
      icon: AlertTriangle,
    },
  ];

  const loading = orders.isLoading || projects.isLoading;
  const error = orders.isError || projects.isError;

  return (
    <>
      <div className="mb-7">
        <p className="text-xs font-bold text-[#8B7F73]">نمای کلی</p>
        <h1 className="mt-1 text-2xl font-black text-[#332A23]">
          وضعیت سفارش‌ها و پروژه‌ها
        </h1>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ title, value, icon: Icon }) => (
          <article
            key={title}
            className="rounded-3xl border border-[#E5DDD2] bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#F0EBE4] text-[#473C33]">
                <Icon size={20} />
              </div>
              <strong className="text-3xl font-black text-[#332A23]">
                {value}
              </strong>
            </div>
            <p className="mt-4 text-sm font-bold text-[#6F6358]">{title}</p>
          </article>
        ))}
      </section>

      {loading && (
        <div className="mt-6 rounded-3xl border border-[#E5DDD2] bg-white p-8 text-sm text-[#776B60]">
          در حال دریافت اطلاعات داشبورد...
        </div>
      )}

      {error && (
        <div className="mt-6 rounded-3xl border border-[#E4BEBE] bg-[#FFF6F6] p-6 text-sm text-[#9B4949]">
          دریافت اطلاعات از Backend ناموفق بود. Backend و تنظیمات
          `NEXT_PUBLIC_API_BASE_URL` را بررسی کنید.
        </div>
      )}

      {!loading && !error && (
        <div className="mt-7 grid gap-7 xl:grid-cols-2">
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-black text-[#332A23]">سفارش‌های اخیر</h2>
              <span className="text-xs text-[#8B7F73]">{orderList.length} مورد</span>
            </div>
            <div className="space-y-4">
              {orderList.slice(0, 5).map((order) => (
                <EntityCard
                  key={order.id}
                  title={order.title}
                  subtitle={`سفارش شماره ${order.id}`}
                  workflow={order.workflow}
                  onTimeline={() =>
                    setSelected({
                      type: 'order',
                      id: order.id,
                      title: order.title,
                    })
                  }
                />
              ))}
              {orderList.length === 0 && (
                <EmptyState text="هنوز سفارشی برای این حساب وجود ندارد." />
              )}
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-black text-[#332A23]">درخواست‌های اخیر</h2>
              <span className="text-xs text-[#8B7F73]">{projectList.length} مورد</span>
            </div>
            <div className="space-y-4">
              {projectList.slice(0, 5).map((project) => (
                <EntityCard
                  key={project.id}
                  title={project.title}
                  subtitle={project.request_type_display || project.request_type}
                  workflow={project.workflow}
                  onTimeline={() =>
                    setSelected({
                      type: 'project',
                      id: project.id,
                      title: project.title,
                    })
                  }
                />
              ))}
              {projectList.length === 0 && (
                <EmptyState text="هنوز درخواستی برای این حساب وجود ندارد." />
              )}
            </div>
          </section>
        </div>
      )}

      <TimelinePanel
        open={Boolean(selected)}
        title={selected?.title || ''}
        loading={
          selected?.type === 'order'
            ? orderTimeline.isLoading
            : projectTimeline.isLoading
        }
        data={
          selected?.type === 'order'
            ? orderTimeline.data
            : projectTimeline.data
        }
        onClose={() => setSelected(null)}
      />
    </>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-[#D9CEC0] bg-white p-8 text-center text-sm text-[#8A7E72]">
      {text}
    </div>
  );
}
