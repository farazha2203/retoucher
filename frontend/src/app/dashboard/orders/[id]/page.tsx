'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ordersAPI } from '@/lib/api/orders';
import { OrderWorkflowPanel } from '@/components/orders/OrderWorkflowPanel';
import type { Order, OrderComment, OrderStatus, OrderTimelineResponse } from '@/types';

const statusLabels: Record<OrderStatus, string> = {
  draft: 'پیش‌نویس',
  submitted: 'ثبت‌شده',
  in_review: 'در حال بررسی',
  assigned: 'اختصاص داده‌شده',
  in_progress: 'در حال انجام',
  delivered: 'تحویل‌شده',
  cancelled: 'لغوشده',
  client_review: 'بررسی کارفرما',
  revision_required: 'نیازمند اصلاح',
  client_revision_requested: 'درخواست اصلاح کارفرما',
  completed: 'تکمیل‌شده',
  settlement_pending: 'در انتظار تسویه',
  paid: 'پرداخت‌شده',
  closed: 'بسته‌شده',
};

const statusStyles: Record<OrderStatus, string> = {
  draft: 'bg-gray-100 text-gray-700',
  submitted: 'bg-blue-50 text-blue-700',
  in_review: 'bg-indigo-50 text-indigo-700',
  assigned: 'bg-violet-50 text-violet-700',
  in_progress: 'bg-amber-50 text-amber-700',
  delivered: 'bg-cyan-50 text-cyan-700',
  cancelled: 'bg-red-50 text-red-700',
  client_review: 'bg-purple-50 text-purple-700',
  revision_required: 'bg-orange-50 text-orange-700',
  client_revision_requested: 'bg-orange-50 text-orange-700',
  completed: 'bg-emerald-50 text-emerald-700',
  settlement_pending: 'bg-yellow-50 text-yellow-700',
  paid: 'bg-green-50 text-green-700',
  closed: 'bg-slate-100 text-slate-700',
};

function formatDate(value?: string | null) {
  if (!value) return '-';

  try {
    return new Intl.DateTimeFormat('fa-IR', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function getStatusLabel(status: OrderStatus) {
  return statusLabels[status] || status;
}

function getStatusClass(status: OrderStatus) {
  return statusStyles[status] || 'bg-gray-100 text-gray-700';
}

function canClientApprove(status: OrderStatus) {
  return status === 'delivered' || status === 'client_review';
}

function canClientRequestRevision(status: OrderStatus) {
  return status === 'delivered' || status === 'client_review';
}

function canClientRate(status: OrderStatus) {
  return status === 'completed' || status === 'paid' || status === 'closed';
}

function canSubmitOrder(status: OrderStatus) {
  return status === 'draft';
}

export default function DashboardOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [order, setOrder] = useState<Order | null>(null);
  const [commentThreads, setCommentThreads] = useState<OrderComment[]>([]);
  const [timeline, setTimeline] = useState<OrderTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');

  const [pageError, setPageError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const [revisionNote, setRevisionNote] = useState('');
  const [ratingScore, setRatingScore] = useState(10);
  const [ratingComment, setRatingComment] = useState('');

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageNote, setImageNote] = useState('');

  const [commentText, setCommentText] = useState('');
  const [replyBoxOpenFor, setReplyBoxOpenFor] = useState<number | null>(null);
  const [replyText, setReplyText] = useState('');

  const clearMessages = () => {
    setPageError('');
    setSuccessMessage('');
  };

  const loadOrder = async () => {
    if (!id) return;

    setLoading(true);
    setPageError('');

    try {
      const [orderData, threadData, timelineData] = await Promise.all([
        ordersAPI.get(id),
        ordersAPI.getCommentThreads(id),
        ordersAPI.timeline(id),
      ]);

      setOrder(orderData);
      setCommentThreads(threadData);
      setTimeline(timelineData);
    } catch {
      setPageError('دریافت اطلاعات سفارش با خطا مواجه شد.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrder();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleSubmitOrder = async () => {
    if (!id) return;

    setActionLoading('submit');
    clearMessages();

    try {
      const updated = await ordersAPI.submit(id);
      setOrder(updated);
      setSuccessMessage('سفارش با موفقیت ارسال شد.');
    } catch {
      setPageError('ارسال سفارش با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  const handleApprove = async () => {
    if (!id) return;

    setActionLoading('approve');
    clearMessages();

    try {
      const updated = await ordersAPI.approve(id);
      setOrder(updated);
      setSuccessMessage('سفارش با موفقیت تایید شد.');
    } catch {
      setPageError('تایید سفارش با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  const handleRequestRevision = async () => {
    if (!id) return;

    if (!revisionNote.trim()) {
      setPageError('لطفاً توضیح اصلاحات را وارد کنید.');
      return;
    }

    setActionLoading('revision');
    clearMessages();

    try {
      const updated = await ordersAPI.requestRevision(id, revisionNote.trim());
      setOrder(updated);
      setRevisionNote('');
      setSuccessMessage('درخواست اصلاح با موفقیت ثبت شد.');
    } catch {
      setPageError('ثبت درخواست اصلاح با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  const handleRate = async () => {
    if (!id) return;

    setActionLoading('rate');
    clearMessages();

    try {
      const updated = await ordersAPI.rate(id, ratingScore, ratingComment);
      if (updated) {
        setOrder(updated as Order);
      } else {
        await loadOrder();
      }
      setRatingComment('');
      setSuccessMessage('امتیاز شما با موفقیت ثبت شد.');
    } catch {
      setPageError('ثبت امتیاز با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  const handleUploadImage = async () => {
    if (!id) return;

    if (!imageFile) {
      setPageError('لطفاً یک تصویر انتخاب کنید.');
      return;
    }

    setActionLoading('upload-image');
    clearMessages();

    try {
      await ordersAPI.uploadImage(id, imageFile, imageNote.trim());
      setImageFile(null);
      setImageNote('');
      const fileInput = document.getElementById('order-image-upload') as HTMLInputElement | null;
      if (fileInput) {
        fileInput.value = '';
      }
      await loadOrder();
      setSuccessMessage('تصویر با موفقیت آپلود شد.');
    } catch {
      setPageError('آپلود تصویر با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  const handleCreateComment = async () => {
    if (!id) return;

    if (!commentText.trim()) {
      setPageError('متن کامنت نمی‌تواند خالی باشد.');
      return;
    }

    setActionLoading('comment');
    clearMessages();

    try {
      await ordersAPI.createComment(id, {
        target_type: 'order',
        text: commentText.trim(),
      });
      setCommentText('');
      await loadOrder();
      setSuccessMessage('کامنت با موفقیت ثبت شد.');
    } catch {
      setPageError('ثبت کامنت با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  const handleReply = async (parentId: number) => {
    if (!id) return;

    if (!replyText.trim()) {
      setPageError('متن پاسخ نمی‌تواند خالی باشد.');
      return;
    }

    setActionLoading(`reply-${parentId}`);
    clearMessages();

    try {
      await ordersAPI.createComment(id, {
        parent: parentId,
        text: replyText.trim(),
      });

      setReplyText('');
      setReplyBoxOpenFor(null);
      await loadOrder();
      setSuccessMessage('پاسخ با موفقیت ثبت شد.');
    } catch {
      setPageError('ثبت پاسخ با خطا مواجه شد.');
    } finally {
      setActionLoading('');
    }
  };

  return (
    <main
      className="min-h-screen px-4 py-10"
      style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
    >
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <Link
            href="/dashboard/orders"
            className="text-sm font-medium text-violet-700 hover:text-violet-800"
          >
            ← بازگشت به سفارش‌ها
          </Link>

          {order && (
            <span className={`rounded-full px-4 py-2 text-xs font-semibold ${getStatusClass(order.status)}`}>
              {getStatusLabel(order.status)}
            </span>
          )}
        </div>

        {loading && (
          <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-gray-500">در حال دریافت اطلاعات سفارش...</p>
          </div>
        )}

        {!loading && pageError && !order && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-center text-sm text-red-600">
            {pageError}
          </div>
        )}

        {!loading && order && (
          <div className="space-y-6">
            <section className="rounded-3xl bg-white p-8 shadow-sm">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{order.title}</h1>
                  <p className="mt-3 text-sm leading-7 text-gray-600">
                    {order.description || 'توضیحی برای این سفارش ثبت نشده است.'}
                  </p>
                </div>

                <div className="shrink-0 rounded-2xl bg-gray-50 p-5 text-center">
                  <div className="text-xs text-gray-400">شناسه سفارش</div>
                  <div className="mt-1 text-2xl font-bold text-gray-900">#{order.id}</div>
                </div>
              </div>

              <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <InfoBox label="کارفرما" value={order.client_username || `#${order.client}`} />
                <InfoBox label="ادیتور" value={order.editor_username || 'اختصاص داده نشده'} />
                <InfoBox label="تاریخ ثبت" value={formatDate(order.created_at)} />
                <InfoBox label="ددلاین" value={formatDate(order.deadline)} />
                <InfoBox label="تعداد اصلاحات" value={String(order.revision_count || 0)} />
                <InfoBox label="تایید ناظر" value={formatDate(order.supervisor_approved_at)} />
                <InfoBox label="تایید کارفرما" value={formatDate(order.client_approved_at)} />
                <InfoBox label="آخرین بروزرسانی" value={formatDate(order.updated_at)} />
              </div>
            </section>

            <OrderWorkflowPanel
              workflow={timeline?.workflow || order.workflow}
              events={timeline?.events || []}
            />

            {(successMessage || pageError) && (
              <section className="rounded-3xl bg-white p-6 shadow-sm">
                {successMessage && (
                  <div className="rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-700">
                    {successMessage}
                  </div>
                )}

                {pageError && (
                  <div className={`${successMessage ? 'mt-3' : ''} rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600`}>
                    {pageError}
                  </div>
                )}
              </section>
            )}

            <section className="rounded-3xl bg-white p-8 shadow-sm">
              <h2 className="mb-5 text-xl font-bold text-gray-900">اقدامات سفارش</h2>

              <div className="grid gap-6 lg:grid-cols-2">
                {canSubmitOrder(order.status) && (
                  <div className="rounded-2xl border border-gray-100 p-5">
                    <h3 className="font-semibold text-gray-900">ارسال سفارش</h3>
                    <p className="mt-2 text-sm leading-6 text-gray-600">
                      بعد از تکمیل اطلاعات اولیه و آپلود تصاویر، سفارش را برای بررسی ارسال کن.
                    </p>

                    <button
                      type="button"
                      onClick={handleSubmitOrder}
                      disabled={actionLoading === 'submit'}
                      className="mt-4 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                    >
                      {actionLoading === 'submit' ? 'در حال ارسال...' : 'ارسال سفارش'}
                    </button>
                  </div>
                )}

                <div className="rounded-2xl border border-gray-100 p-5">
                  <h3 className="font-semibold text-gray-900">آپلود تصویر</h3>
                  <p className="mt-2 text-sm leading-6 text-gray-600">
                    تصاویر اصلی سفارش را برای شروع کار آپلود کن.
                  </p>

                  <input
                    id="order-image-upload"
                    type="file"
                    accept="image/*"
                    onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
                    className="mt-4 block w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm"
                  />

                  <input
                    value={imageNote}
                    onChange={(e) => setImageNote(e.target.value)}
                    placeholder="توضیح تصویر، اختیاری"
                    className="mt-3 w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
                  />

                  <button
                    type="button"
                    onClick={handleUploadImage}
                    disabled={actionLoading === 'upload-image'}
                    className="mt-4 rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-50"
                  >
                    {actionLoading === 'upload-image' ? 'در حال آپلود...' : 'آپلود تصویر'}
                  </button>
                </div>

                {canClientApprove(order.status) && (
                  <div className="rounded-2xl border border-gray-100 p-5">
                    <h3 className="font-semibold text-gray-900">تایید نهایی سفارش</h3>
                    <p className="mt-2 text-sm leading-6 text-gray-600">
                      اگر فایل تحویلی مورد تایید شماست، سفارش را تایید کنید.
                    </p>

                    <button
                      type="button"
                      onClick={handleApprove}
                      disabled={actionLoading === 'approve'}
                      className="mt-4 rounded-2xl bg-emerald-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
                    >
                      {actionLoading === 'approve' ? 'در حال تایید...' : 'تایید سفارش'}
                    </button>
                  </div>
                )}

                {canClientRequestRevision(order.status) && (
                  <div className="rounded-2xl border border-gray-100 p-5">
                    <h3 className="font-semibold text-gray-900">درخواست اصلاح</h3>

                    <textarea
                      value={revisionNote}
                      onChange={(e) => setRevisionNote(e.target.value)}
                      rows={4}
                      placeholder="توضیحات اصلاحات..."
                      className="mt-4 w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
                    />

                    <button
                      type="button"
                      onClick={handleRequestRevision}
                      disabled={actionLoading === 'revision'}
                      className="mt-4 rounded-2xl bg-orange-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-orange-700 disabled:opacity-50"
                    >
                      {actionLoading === 'revision' ? 'در حال ثبت...' : 'ثبت درخواست اصلاح'}
                    </button>
                  </div>
                )}

                {canClientRate(order.status) && (
                  <div className="rounded-2xl border border-gray-100 p-5">
                    <h3 className="font-semibold text-gray-900">امتیازدهی</h3>

                    <div className="mt-4 grid gap-4 sm:grid-cols-[160px_1fr]">
                      <select
                        value={ratingScore}
                        onChange={(e) => setRatingScore(Number(e.target.value))}
                        className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
                      >
                        {Array.from({ length: 10 }, (_, i) => i + 1).map((score) => (
                          <option key={score} value={score}>
                            {score}
                          </option>
                        ))}
                      </select>

                      <input
                        value={ratingComment}
                        onChange={(e) => setRatingComment(e.target.value)}
                        placeholder="نظر شما..."
                        className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
                      />
                    </div>

                    <button
                      type="button"
                      onClick={handleRate}
                      disabled={actionLoading === 'rate'}
                      className="mt-4 rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-50"
                    >
                      {actionLoading === 'rate' ? 'در حال ثبت...' : 'ثبت امتیاز'}
                    </button>
                  </div>
                )}
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <Panel title="تصاویر سفارش">
                {order.images && order.images.length > 0 ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {order.images.map((image) => (
                      <div key={image.id} className="overflow-hidden rounded-2xl border border-gray-100">
                        <img
                          src={image.image}
                          alt={image.note || 'order image'}
                          className="h-48 w-full object-cover"
                        />
                        <div className="p-3">
                          <div className="text-sm text-gray-700">{image.note || 'بدون توضیح'}</div>
                          <div className="mt-1 text-xs text-gray-400">{formatDate(image.uploaded_at)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyText text="تصویری ثبت نشده است." />
                )}
              </Panel>

              <Panel title="فایل‌های تحویلی">
                {order.deliveries && order.deliveries.length > 0 ? (
                  <div className="space-y-3">
                    {order.deliveries.map((delivery) => (
                      <div key={delivery.id} className="rounded-2xl border border-gray-100 p-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <div className="font-semibold text-gray-900">
                              فایل تحویلی #{delivery.id}
                            </div>
                            <div className="mt-1 text-xs text-gray-500">
                              توسط: {delivery.uploaded_by_username || '-'}
                            </div>
                          </div>

                          <a
                            href={delivery.file}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-xl bg-gray-900 px-4 py-2 text-xs font-medium text-white"
                          >
                            دانلود / مشاهده
                          </a>
                        </div>

                        {delivery.note && (
                          <p className="mt-3 text-sm leading-6 text-gray-600">{delivery.note}</p>
                        )}

                        <div className="mt-3 text-xs text-gray-400">
                          {formatDate(delivery.uploaded_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyText text="هنوز فایلی تحویل نشده است." />
                )}
              </Panel>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <Panel title="ثبت کامنت جدید">
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={5}
                  placeholder="کامنت یا توضیح جدید برای این سفارش..."
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
                />

                <button
                  type="button"
                  onClick={handleCreateComment}
                  disabled={actionLoading === 'comment'}
                  className="mt-4 rounded-2xl bg-violet-700 px-5 py-3 text-sm font-medium text-white transition hover:bg-violet-800 disabled:opacity-50"
                >
                  {actionLoading === 'comment' ? 'در حال ثبت...' : 'ثبت کامنت'}
                </button>
              </Panel>

              <Panel title="گفتگوها / Thread Comments">
                {commentThreads.length > 0 ? (
                  <div className="space-y-4">
                    {commentThreads.map((comment) => (
                      <CommentThreadCard
                        key={comment.id}
                        comment={comment}
                        replyBoxOpenFor={replyBoxOpenFor}
                        setReplyBoxOpenFor={setReplyBoxOpenFor}
                        replyText={replyText}
                        setReplyText={setReplyText}
                        onReply={handleReply}
                        actionLoading={actionLoading}
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyText text="هنوز thread commentی ثبت نشده است." />
                )}
              </Panel>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <Panel title="اصلاحات">
                {order.revisions && order.revisions.length > 0 ? (
                  <div className="space-y-3">
                    {order.revisions.map((revision) => (
                      <div key={revision.id} className="rounded-2xl border border-gray-100 p-4">
                        <div className="text-sm font-semibold text-gray-900">
                          {revision.source === 'client' ? 'درخواست کارفرما' : 'درخواست ناظر'}
                        </div>
                        <p className="mt-2 text-sm leading-6 text-gray-600">{revision.note}</p>
                        <div className="mt-3 text-xs text-gray-400">
                          {revision.requested_by_username || '-'} - {formatDate(revision.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyText text="درخواستی برای اصلاح ثبت نشده است." />
                )}
              </Panel>

              <Panel title="امتیازها">
                {order.ratings && order.ratings.length > 0 ? (
                  <div className="space-y-3">
                    {order.ratings.map((rating) => (
                      <div key={rating.id} className="rounded-2xl border border-gray-100 p-4">
                        <div className="font-semibold text-gray-900">
                          امتیاز {rating.score}/10
                        </div>

                        {rating.comment && (
                          <p className="mt-2 text-sm leading-6 text-gray-600">{rating.comment}</p>
                        )}

                        <div className="mt-3 text-xs text-gray-400">
                          {rating.rated_by_username || '-'} - {formatDate(rating.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyText text="امتیازی ثبت نشده است." />
                )}
              </Panel>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <Panel title="تاریخچه وضعیت">
                {order.status_history && order.status_history.length > 0 ? (
                  <div className="space-y-3">
                    {order.status_history.map((item) => (
                      <div key={item.id} className="rounded-2xl border border-gray-100 p-4">
                        <div className="text-sm font-semibold text-gray-900">
                          {item.from_status || '-'} → {item.to_status}
                        </div>

                        {item.note && (
                          <p className="mt-2 text-sm leading-6 text-gray-600">{item.note}</p>
                        )}

                        <div className="mt-3 text-xs text-gray-400">
                          {item.changed_by_username || '-'} - {formatDate(item.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyText text="تاریخچه‌ای ثبت نشده است." />
                )}
              </Panel>

              <Panel title="لاگ فعالیت‌ها">
                {order.activity_logs && order.activity_logs.length > 0 ? (
                  <div className="space-y-3">
                    {order.activity_logs.map((log) => (
                      <div key={log.id} className="rounded-2xl border border-gray-100 p-4">
                        <div className="text-sm font-semibold text-gray-900">
                          {log.activity_type}
                        </div>

                        {log.message && (
                          <p className="mt-2 text-sm leading-6 text-gray-600">{log.message}</p>
                        )}

                        <div className="mt-3 text-xs text-gray-400">
                          {log.actor_username || '-'} - {formatDate(log.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyText text="لاگی ثبت نشده است." />
                )}
              </Panel>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

function CommentThreadCard({
  comment,
  replyBoxOpenFor,
  setReplyBoxOpenFor,
  replyText,
  setReplyText,
  onReply,
  actionLoading,
  level = 0,
}: {
  comment: OrderComment;
  replyBoxOpenFor: number | null;
  setReplyBoxOpenFor: (value: number | null) => void;
  replyText: string;
  setReplyText: (value: string) => void;
  onReply: (parentId: number) => void;
  actionLoading: string;
  level?: number;
}) {
  return (
    <div
      className={`rounded-2xl border border-gray-100 p-4 ${level > 0 ? 'mr-4 mt-3 bg-gray-50' : 'bg-white'}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="font-semibold text-gray-900">
          {comment.sender_username || 'کاربر حذف‌شده'}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
            {comment.target_type}
          </span>

          {comment.is_resolved && (
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
              resolved
            </span>
          )}
        </div>
      </div>

      <p className="mt-2 text-sm leading-6 text-gray-600">{comment.text || '-'}</p>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-gray-400">{formatDate(comment.created_at)}</div>

        <button
          type="button"
          onClick={() =>
            setReplyBoxOpenFor(replyBoxOpenFor === comment.id ? null : comment.id)
          }
          className="text-xs font-medium text-violet-700 hover:text-violet-800"
        >
          پاسخ
        </button>
      </div>

      {replyBoxOpenFor === comment.id && (
        <div className="mt-4 rounded-2xl border border-violet-100 bg-violet-50 p-4">
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            rows={3}
            placeholder="متن پاسخ..."
            className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm outline-none focus:border-violet-300"
          />

          <div className="mt-3 flex gap-3">
            <button
              type="button"
              onClick={() => onReply(comment.id)}
              disabled={actionLoading === `reply-${comment.id}`}
              className="rounded-2xl bg-violet-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-violet-800 disabled:opacity-50"
            >
              {actionLoading === `reply-${comment.id}` ? 'در حال ثبت...' : 'ثبت پاسخ'}
            </button>

            <button
              type="button"
              onClick={() => {
                setReplyBoxOpenFor(null);
                setReplyText('');
              }}
              className="rounded-2xl bg-white px-4 py-2 text-sm font-medium text-gray-700 ring-1 ring-gray-200"
            >
              انصراف
            </button>
          </div>
        </div>
      )}

      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3">
          {comment.replies.map((reply) => (
            <CommentThreadCard
              key={reply.id}
              comment={reply}
              replyBoxOpenFor={replyBoxOpenFor}
              setReplyBoxOpenFor={setReplyBoxOpenFor}
              replyText={replyText}
              setReplyText={setReplyText}
              onReply={onReply}
              actionLoading={actionLoading}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-gray-50 p-4">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-gray-800">{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-3xl bg-white p-8 shadow-sm">
      <h2 className="mb-5 text-xl font-bold text-gray-900">{title}</h2>
      {children}
    </section>
  );
}

function EmptyText({ text }: { text: string }) {
  return <p className="text-sm text-gray-500">{text}</p>;
}
