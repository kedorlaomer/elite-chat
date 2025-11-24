from chat.models import Message

class UnapprovedMessage(Message):
    class Meta:
        proxy = True
        app_label = 'moderation'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
