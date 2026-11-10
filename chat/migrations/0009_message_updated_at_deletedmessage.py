from django.db import migrations, models
from django.db.models import F
from django.utils import timezone


def backfill_updated_at(apps, schema_editor):
    Message = apps.get_model('chat', 'Message')
    Message.objects.update(updated_at=F('created_at'))


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_image_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_updated_at, migrations.RunPython.noop),
        migrations.CreateModel(
            name='DeletedMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.BigIntegerField()),
                ('room_id', models.BigIntegerField()),
                ('deleted_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'indexes': [models.Index(fields=['room_id', 'deleted_at'], name='chat_deleted_room_time_idx')],
            },
        ),
    ]
