'use client';

import { EntityCard } from '@/components/workflow/EntityCard';
import { TimelinePanel } from '@/components/workflow/TimelinePanel';
import { useOrders, useOrderTimeline } from '@/lib/hooks/useOrders';
import { useState } from 'react';

export default function OrdersPage() {
  const orders = useOrders();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const timeline = useOrderTimeline(selectedId);
  const selected = orders.data?.find((item) => item.id === selectedId);

  return (
    <>
      <Header title="سفارش‌ها" description="پیگیری مرحله، پیشرفت و ضرب‌الاجل سفارش‌ها" />
      <div className="grid gap-4 xl:grid-cols-2">
        {orders.data?.map((order) => (
          <EntityCard
            key={order.id}
            title={order.title}
            subtitle={order.status_display || order.status}
            workflow={order.workflow}
            onTimeline={() => setSelectedId(order.id)}
          />
        ))}
      </div>
      {!orders.isLoading && orders.data?.length === 0 && (
        <p className="rounded-3xl border border-dashed border-[#D9CEC0] bg-white p-8 text-center text-sm text-[#8A7E72]">
          سفارشی موجود نیست.
        </p>
      )}
      <TimelinePanel
        open={selectedId !== null}
        title={selected?.title || 'سفارش'}
        loading={timeline.isLoading}
        data={timeline.data}
        onClose={() => setSelectedId(null)}
      />
    </>
  );
}

function Header({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-7">
      <h1 className="text-2xl font-black text-[#332A23]">{title}</h1>
      <p className="mt-2 text-sm text-[#82766A]">{description}</p>
    </div>
  );
}
