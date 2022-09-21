""" alert a user to activity """
from django.db import models, transaction
from django.utils import timezone
from django.dispatch import receiver
from .base_model import BookWyrmModel
from .book import Genre, Book, Work, Edition
from . import Boost, Favorite, GroupMemberInvitation, ImportJob, ListItem, Report
from . import Status, User, UserFollowRequest, Book

class GenreNotification(BookWyrmModel):
    """a book has been added to a genre you follow"""
    from_genre = models.ForeignKey(Genre, related_name="notification_from", on_delete=models.CASCADE, null=True)
    related_users = models.ManyToManyField("User", symmetrical=False, related_name="notifications_to", null=True)
    book = models.ForeignKey(Book, related_name="+", on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    GENRE = "GENRE"

    class Meta:
        ordering = ("-created",)
        #Speed up notifcation queries
        #index_together = ("related_users","read")
        abstract = False

class GenreNotificationQuerySet(models.query.QuerySet):
    def unread(self):
        return self.filter(unread=True)

    def read(self):
        return self.filter(unread=False)

    def mark_all_as_read(self, to_user):
        qs = self.unread(True)
        if to_user:
            qs = qs.filter(to_user=to_user)
        return qs.update(unread=True)

    def delete_all(self, to_user):
        qs = qs.filter(to_user=to_user)
        delete()

class FollowedGenre(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    genres = models.ManyToManyField(Genre, blank=True)
    created = models.DateTimeField(default=timezone.now)

class Notification(BookWyrmModel):
    """you've been tagged, liked, followed, etc"""

    # Status interactions
    FAVORITE = "FAVORITE"
    BOOST = "BOOST"
    REPLY = "REPLY"
    MENTION = "MENTION"
    TAG = "TAG"

    # Genre update
    GENRE = "GENRE"

    # Relationships
    FOLLOW = "FOLLOW"
    FOLLOW_REQUEST = "FOLLOW_REQUEST"

    # Imports
    IMPORT = "IMPORT"

    # List activity
    ADD = "ADD"

    # Admin
    REPORT = "REPORT"

    # Groups
    INVITE = "INVITE"
    ACCEPT = "ACCEPT"
    JOIN = "JOIN"
    LEAVE = "LEAVE"
    REMOVE = "REMOVE"
    GROUP_PRIVACY = "GROUP_PRIVACY"
    GROUP_NAME = "GROUP_NAME"
    GROUP_DESCRIPTION = "GROUP_DESCRIPTION"

    # pylint: disable=line-too-long
    NotificationType = models.TextChoices(
        # there has got be a better way to do this
        "NotificationType",
        f"{GENRE} {FAVORITE} {REPLY} {MENTION} {TAG} {FOLLOW} {FOLLOW_REQUEST} {BOOST} {IMPORT} {ADD} {REPORT} {INVITE} {ACCEPT} {JOIN} {LEAVE} {REMOVE} {GROUP_PRIVACY} {GROUP_NAME} {GROUP_DESCRIPTION}",
    )

    user = models.ForeignKey("User", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=255, choices=NotificationType.choices
    )

    related_genre = models.ForeignKey("Genre", on_delete=models.CASCADE, null=True, related_name="notifications")

    related_users = models.ManyToManyField(
        "User", symmetrical=False, related_name="notifications"
    )
    related_group = models.ForeignKey(
        "Group", on_delete=models.CASCADE, null=True, related_name="notifications"
    )
    related_status = models.ForeignKey("Status", on_delete=models.CASCADE, null=True)
    related_import = models.ForeignKey("ImportJob", on_delete=models.CASCADE, null=True)
    related_list_items = models.ManyToManyField(
        "ListItem", symmetrical=False, related_name="notifications"
    )
    related_reports = models.ManyToManyField("Report", symmetrical=False)

    @classmethod
    @transaction.atomic
    def notify(cls, user, related_user, **kwargs):
        """Create a notification"""
        if related_user and (not user.local or user == related_user):
            return
        notification = cls.objects.filter(user=user, **kwargs).first()
        if not notification:
            notification = cls.objects.create(user=user, **kwargs)
        if related_user:
            notification.related_users.add(related_user)
        notification.read = False
        notification.save()

    """Create genre notification - UPDATE"""
    @classmethod
    @transaction.atomic
    def notify_genre_update(cls, users, **kwargs):
        """Notify on genre activity"""
        notification = cls.objects.create(**kwargs)
        for user in users:
            notification.related_users.add(user.user)
        notification.read = False
        notification.save()

    @classmethod
    @transaction.atomic
    def notify_list_item(cls, user, list_item):
        """Group the notifications around the list items, not the user"""
        related_user = list_item.user
        notification = cls.objects.filter(
            user=user,
            related_users=related_user,
            related_list_items__book_list=list_item.book_list,
            notification_type=Notification.ADD,
        ).first()
        if not notification:
            notification = cls.objects.create(
                user=user, notification_type=Notification.ADD
            )
            notification.related_users.add(related_user)
        notification.related_list_items.add(list_item)
        notification.read = False
        notification.save()

    @classmethod
    def unnotify(cls, user, related_user, **kwargs):
        """Remove a user from a notification and delete it if that was the only user"""
        try:
            notification = cls.objects.filter(user=user, **kwargs).get()
        except Notification.DoesNotExist:
            return
        notification.related_users.remove(related_user)
        if not notification.related_users.count():
            notification.delete()

"""Receiver for genre update - UPDATE"""
@receiver(models.signals.m2m_changed, sender=Edition.genres.through)
def genre_update(sender, instance, action, pk_set, reverse, **kwargs):
    if action == "post_add":
        for key in pk_set:
            genre = Genre.objects.get(pk=key)
            users = FollowedGenre.objects.filter(genres=genre)
            Notification.notify_genre_update(users,
            user = instance.last_edited_by,
            related_genre=genre,
            notification_type=Notification.GENRE
            )


@receiver(models.signals.post_save, sender=Favorite)
# pylint: disable=unused-argument
def notify_on_fav(sender, instance, *args, **kwargs):
    """someone liked your content, you ARE loved"""
    Notification.notify(
        instance.status.user,
        instance.user,
        related_status=instance.status,
        notification_type=Notification.FAVORITE,
    )


@receiver(models.signals.post_delete, sender=Favorite)
# pylint: disable=unused-argument
def notify_on_unfav(sender, instance, *args, **kwargs):
    """oops, didn't like that after all"""
    if not instance.status.user.local:
        return
    Notification.unnotify(
        instance.status.user,
        instance.user,
        related_status=instance.status,
        notification_type=Notification.FAVORITE,
    )


@receiver(models.signals.post_save)
@transaction.atomic
# pylint: disable=unused-argument
def notify_user_on_mention(sender, instance, *args, **kwargs):
    """creating and deleting statuses with @ mentions and replies"""
    if not issubclass(sender, Status):
        return

    if instance.deleted:
        Notification.objects.filter(related_status=instance).delete()
        return

    if (
        instance.reply_parent
        and instance.reply_parent.user != instance.user
        and instance.reply_parent.user.local
    ):
        Notification.notify(
            instance.reply_parent.user,
            instance.user,
            related_status=instance,
            notification_type=Notification.REPLY,
        )

    for mention_user in instance.mention_users.all():
        # avoid double-notifying about this status
        if not mention_user.local or (
            instance.reply_parent and mention_user == instance.reply_parent.user
        ):
            continue
        Notification.notify(
            mention_user,
            instance.user,
            notification_type=Notification.MENTION,
            related_status=instance,
        )


@receiver(models.signals.post_save, sender=Boost)
# pylint: disable=unused-argument
def notify_user_on_boost(sender, instance, *args, **kwargs):
    """boosting a status"""
    if (
        not instance.boosted_status.user.local
        or instance.boosted_status.user == instance.user
    ):
        return

    Notification.notify(
        instance.boosted_status.user,
        instance.user,
        related_status=instance.boosted_status,
        notification_type=Notification.BOOST,
    )


@receiver(models.signals.post_delete, sender=Boost)
# pylint: disable=unused-argument
def notify_user_on_unboost(sender, instance, *args, **kwargs):
    """unboosting a status"""
    Notification.unnotify(
        instance.boosted_status.user,
        instance.user,
        related_status=instance.boosted_status,
        notification_type=Notification.BOOST,
    )


@receiver(models.signals.post_save, sender=ImportJob)
# pylint: disable=unused-argument
def notify_user_on_import_complete(
    sender, instance, *args, update_fields=None, **kwargs
):
    """we imported your books! aren't you proud of us"""
    update_fields = update_fields or []
    if not instance.complete or "complete" not in update_fields:
        return
    Notification.objects.create(
        user=instance.user,
        notification_type=Notification.IMPORT,
        related_import=instance,
    )


@receiver(models.signals.post_save, sender=Report)
@transaction.atomic
# pylint: disable=unused-argument
def notify_admins_on_report(sender, instance, created, *args, **kwargs):
    """something is up, make sure the admins know"""
    if not created:
        # otherwise you'll get a notification when you resolve a report
        return

    # moderators and superusers should be notified
    admins = User.admins()
    for admin in admins:
        notification, _ = Notification.objects.get_or_create(
            user=admin,
            notification_type=Notification.REPORT,
            read=False,
        )
        notification.related_reports.add(instance)


@receiver(models.signals.post_save, sender=GroupMemberInvitation)
# pylint: disable=unused-argument
def notify_user_on_group_invite(sender, instance, *args, **kwargs):
    """Cool kids club here we come"""
    Notification.notify(
        instance.user,
        instance.group.user,
        related_group=instance.group,
        notification_type=Notification.INVITE,
    )


@receiver(models.signals.post_save, sender=ListItem)
@transaction.atomic
# pylint: disable=unused-argument
def notify_user_on_list_item_add(sender, instance, created, *args, **kwargs):
    """Someone added to your list"""
    if not created:
        return

    list_owner = instance.book_list.user
    # create a notification if somoene ELSE added to a local user's list
    if list_owner.local and list_owner != instance.user:
        # keep the related_user singular, group the items
        Notification.notify_list_item(list_owner, instance)

    if instance.book_list.group:
        for membership in instance.book_list.group.memberships.all():
            if membership.user != instance.user:
                Notification.notify_list_item(membership.user, instance)


@receiver(models.signals.post_save, sender=UserFollowRequest)
@transaction.atomic
# pylint: disable=unused-argument
def notify_user_on_follow(sender, instance, created, *args, **kwargs):
    """Someone added to your list"""
    if not created or not instance.user_object.local:
        return

    manually_approves = instance.user_object.manually_approves_followers
    if manually_approves:
        # don't group notifications
        notification = Notification.objects.filter(
            user=instance.user_object,
            related_users=instance.user_subject,
            notification_type=Notification.FOLLOW_REQUEST,
        ).first()
        if not notification:
            notification = Notification.objects.create(
                user=instance.user_object, notification_type=Notification.FOLLOW_REQUEST
            )
        notification.related_users.set([instance.user_subject])
        notification.read = False
        notification.save()
    else:
        # Only group unread follows
        Notification.notify(
            instance.user_object,
            instance.user_subject,
            notification_type=Notification.FOLLOW,
            read=False,
        )
