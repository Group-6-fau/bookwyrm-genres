""" instance overview """
from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from bookwyrm import models


# pylint: disable= no-self-use
@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("bookwyrm.moderate_user", raise_exception=True),
    name="dispatch",
)
class Dashboard(View):
    """admin overview"""

    def get(self, request):
        """list of users"""
        buckets = 6
        bucket_size = 1  # days
        now = timezone.now()

        user_queryset = models.User.objects.filter(local=True, is_active=True)

        user_stats = {"labels": [], "total": [], "active": []}
        interval_end = now - timedelta(days=buckets * bucket_size)
        while interval_end < timezone.now():
            user_stats["total"].append(
                user_queryset.filter(created_date__day__lte=interval_end.day).count()
            )
            user_stats["active"].append(
                user_queryset.filter(
                    last_active_date__gt=interval_end - timedelta(days=31),
                    created_date__day__lte=interval_end.day,
                ).count()
            )
            user_stats["labels"].append(interval_end.strftime("%b %d"))
            interval_end += timedelta(days=bucket_size)

        status_queryset = models.Status.objects.filter(user__local=True, deleted=False)
        status_stats = {"labels": [], "total": []}
        interval_start = now - timedelta(days=buckets * bucket_size)
        interval_end = interval_start + timedelta(days=bucket_size)
        while interval_end < timezone.now():
            status_stats["total"].append(
                status_queryset.filter(
                    created_date__day__gt=interval_start.day,
                    created_date__day__lte=interval_end.day,
                ).count()
            )
            status_stats["labels"].append(interval_end.strftime("%b %d"))
            interval_start = interval_end
            interval_end += timedelta(days=bucket_size)

        data = {
            "users": user_queryset.count(),
            "active_users": user_queryset.filter(
                last_active_date__gte=now - timedelta(days=31)
            ).count(),
            "statuses": status_queryset.count(),
            "works": models.Work.objects.count(),
            "reports": models.Report.objects.filter(resolved=False).count(),
            "invite_requests": models.InviteRequest.objects.filter(
                ignored=False, invite_sent=False
            ).count(),
            "user_stats": user_stats,
            "status_stats": status_stats,
        }
        return TemplateResponse(request, "settings/dashboard.html", data)
