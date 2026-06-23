from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import (
    Order,
    OrderActivityLog,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderNotification,
    OrderRating,
)


class Command(BaseCommand):
    help = "Create or refresh demo users and demo order data for Retoucher Phase 1."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove previous demo order related data before recreating it.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        with transaction.atomic():
            client = self.ensure_user(
                username="client01",
                password="ClientPass123!",
                role="client",
                is_staff=False,
                is_superuser=False,
            )
            editor = self.ensure_user(
                username="editor01",
                password="EditorPass123!",
                role="editor",
                is_staff=False,
                is_superuser=False,
            )
            support = self.ensure_user(
                username="support01",
                password="SupportPass123!",
                role="support",
                is_staff=True,
                is_superuser=False,
            )
            supervisor = self.ensure_user(
                username="supervisor01",
                password="SupervisorPass123!",
                role="supervisor",
                is_staff=True,
                is_superuser=False,
            )

            if reset:
                self.reset_demo_order()

            order = self.ensure_demo_order(
                client=client,
                editor=editor,
            )

            self.create_demo_files(
                order=order,
                editor=editor,
            )

            self.create_demo_comments(
                order=order,
                support=support,
                editor=editor,
                client=client,
            )

            self.create_demo_ratings(
                order=order,
                client=client,
                supervisor=supervisor,
            )

            self.create_demo_activity_logs(
                order=order,
                support=support,
                editor=editor,
                client=client,
                supervisor=supervisor,
            )

            self.create_demo_notifications(
                order=order,
                support=support,
                editor=editor,
                client=client,
            )

        self.stdout.write(self.style.SUCCESS("Demo data created successfully."))
        self.stdout.write("")
        self.stdout.write("Demo users:")
        self.stdout.write("  client01 / ClientPass123!")
        self.stdout.write("  editor01 / EditorPass123!")
        self.stdout.write("  support01 / SupportPass123!")
        self.stdout.write("  supervisor01 / SupervisorPass123!")
        self.stdout.write("")
        self.stdout.write(f"Demo order id: {order.id}")
        self.stdout.write(f"Demo order title: {order.title}")

    def ensure_user(
        self,
        username,
        password,
        role,
        is_staff=False,
        is_superuser=False,
    ):
        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "role": role,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )

        changed_fields = []

        if getattr(user, "role", None) != role:
            user.role = role
            changed_fields.append("role")

        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed_fields.append("is_staff")

        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed_fields.append("is_superuser")

        if not user.is_active:
            user.is_active = True
            changed_fields.append("is_active")

        user.set_password(password)
        changed_fields.append("password")

        user.save(update_fields=changed_fields)

        if created:
            self.stdout.write(f"Created user: {username}")
        else:
            self.stdout.write(f"Updated user: {username}")

        return user

    def reset_demo_order(self):
        demo_orders = Order.objects.filter(title="Wedding photo retouch")

        order_ids = list(demo_orders.values_list("id", flat=True))

        if not order_ids:
            return

        OrderNotification.objects.filter(order_id__in=order_ids).delete()
        OrderActivityLog.objects.filter(order_id__in=order_ids).delete()
        OrderComment.objects.filter(order_id__in=order_ids).delete()
        OrderRating.objects.filter(order_id__in=order_ids).delete()
        OrderDelivery.objects.filter(order_id__in=order_ids).delete()
        OrderImage.objects.filter(order_id__in=order_ids).delete()
        demo_orders.delete()

        self.stdout.write("Previous demo order data removed.")

    def ensure_demo_order(self, client, editor):
        order, created = Order.objects.get_or_create(
            title="Wedding photo retouch",
            client=client,
            defaults={
                "editor": editor,
                "description": "Please retouch skin, color, and background for this wedding photo.",
                "deadline": timezone.now() + timedelta(days=7),
            },
        )

        update_fields = []

        if order.editor_id != editor.id:
            order.editor = editor
            update_fields.append("editor")

        if not order.description:
            order.description = (
                "Please retouch skin, color, and background for this wedding photo."
            )
            update_fields.append("description")

        if order.deadline is None:
            order.deadline = timezone.now() + timedelta(days=7)
            update_fields.append("deadline")

        if update_fields:
            order.save(update_fields=update_fields)

        # Make the demo order visually useful in admin/dashboard without relying on workflow actions.
        if hasattr(Order, "Status"):
            target_status = getattr(Order.Status, "CLIENT_REVIEW", None)
            if target_status is not None:
                Order.objects.filter(pk=order.pk).update(status=target_status)
                order.refresh_from_db()

        if created:
            self.stdout.write(f"Created demo order: {order.title}")
        else:
            self.stdout.write(f"Updated demo order: {order.title}")

        return order

    def create_demo_files(self, order, editor):
        if not OrderImage.objects.filter(
            order=order, note="[Demo] Original wedding photo"
        ).exists():
            OrderImage.objects.create(
                order=order,
                image=ContentFile(
                    b"demo original image content",
                    name="demo-original-wedding-photo.jpg",
                ),
                note="[Demo] Original wedding photo",
            )

        if not OrderDelivery.objects.filter(
            order=order, note="[Demo] Final edited delivery"
        ).exists():
            OrderDelivery.objects.create(
                order=order,
                uploaded_by=editor,
                file=ContentFile(
                    b"demo final edited delivery content",
                    name="demo-final-delivery.jpg",
                ),
                note="[Demo] Final edited delivery",
            )

    def create_demo_comments(self, order, support, editor, client):
        root_comment, _ = OrderComment.objects.get_or_create(
            order=order,
            sender=support,
            target_type="order",
            text="[Demo] Please review the latest delivery carefully.",
            defaults={
                "status": "active",
            },
        )

        OrderComment.objects.get_or_create(
            order=order,
            sender=client,
            parent=root_comment,
            target_type="order",
            text="[Demo] Looks good, but I prefer warmer colors.",
            defaults={
                "status": "active",
            },
        )

        delivery = OrderDelivery.objects.filter(order=order).first()

        if delivery is not None:
            OrderComment.objects.get_or_create(
                order=order,
                sender=support,
                target_type="delivery",
                delivery=delivery,
                text="[Demo] Please reduce smoothing around this skin area.",
                defaults={
                    "x": 42.5,
                    "y": 58.3,
                    "status": "active",
                    "annotation_type": "point",
                    "annotation_label": "Skin smoothing",
                    "annotation_color": "#ff0000",
                    "annotation_data": {
                        "priority": "high",
                        "tool": "pin",
                    },
                },
            )

        image = OrderImage.objects.filter(order=order).first()

        if image is not None:
            OrderComment.objects.get_or_create(
                order=order,
                sender=editor,
                target_type="image",
                image=image,
                text="[Demo] Background color adjustment area.",
                defaults={
                    "x": 20,
                    "y": 30,
                    "status": "active",
                    "annotation_type": "rectangle",
                    "annotation_label": "Background area",
                    "annotation_color": "#00ff00",
                    "annotation_data": {
                        "width": 25,
                        "height": 15,
                    },
                },
            )

    def create_demo_ratings(self, order, client, supervisor):
        OrderRating.objects.update_or_create(
            order=order,
            source="client",
            defaults={
                "rated_by": client,
                "score": 8,
                "comment": "[Demo] Good quality, but warmer colors would be better.",
            },
        )

        OrderRating.objects.update_or_create(
            order=order,
            source="supervisor",
            defaults={
                "rated_by": supervisor,
                "score": 9,
                "comment": "[Demo] Delivery quality is approved for client review.",
            },
        )

        OrderRating.objects.update_or_create(
            order=order,
            source="supervisor",
            defaults={
                "score": 9,
                "comment": "[Demo] Delivery quality is approved for client review.",
            },
        )

    def create_demo_activity_logs(self, order, support, editor, client, supervisor):
        demo_logs = [
            (
                support,
                "editor_assigned",
                "[Demo] Editor assigned to order.",
                {"editor_username": editor.username},
            ),
            (
                editor,
                "delivery_uploaded",
                "[Demo] Editor uploaded delivery file.",
                {"delivery_note": "Final edited delivery"},
            ),
            (
                supervisor,
                "status_changed",
                "[Demo] Supervisor approved delivery for client review.",
                {"status": "client_review"},
            ),
            (
                client,
                "comment_created",
                "[Demo] Client submitted feedback.",
                {"target_type": "order"},
            ),
        ]

        for actor, activity_type, message, metadata in demo_logs:
            exists = OrderActivityLog.objects.filter(
                order=order,
                actor=actor,
                activity_type=activity_type,
                message=message,
            ).exists()

            if not exists:
                OrderActivityLog.objects.create(
                    order=order,
                    actor=actor,
                    activity_type=activity_type,
                    message=message,
                    metadata=metadata,
                )

    def create_demo_notifications(self, order, support, editor, client):
        notification_payloads = [
            (
                client,
                support,
                "comment_created",
                "New comment",
                "[Demo] Support added a comment to your order.",
                {"demo": True},
            ),
            (
                editor,
                support,
                "comment_created",
                "New comment",
                "[Demo] Support added a comment to an assigned order.",
                {"demo": True},
            ),
        ]

        for (
            recipient,
            actor,
            notification_type,
            title,
            message,
            metadata,
        ) in notification_payloads:
            exists = OrderNotification.objects.filter(
                order=order,
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
            ).exists()

            if not exists:
                OrderNotification.objects.create(
                    order=order,
                    recipient=recipient,
                    actor=actor,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    metadata=metadata,
                )
