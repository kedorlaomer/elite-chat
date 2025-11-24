from chat.models import Message

class UnapprovedMessage(Message):
    class Meta:
        proxy = True
        app_label = 'moderation'
        verbose_name = 'Unapproved Message'
        verbose_name_plural = 'Unapproved Messages'

class AllMessage(Message):
    class Meta:
        proxy = True
        app_label = 'moderation'
        verbose_name = 'All Message'
        verbose_name_plural = 'All Messages'
