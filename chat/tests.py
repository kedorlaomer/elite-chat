from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from .models import DeletedMessage, Image, Membership, Message, Profile, Room
from .views import POLL_OVERLAP


class PollingTestCase(TestCase):
    def setUp(self):
        # LANGUAGE_CODE 'en-us' isn't in LANGUAGES, so reverse() before any
        # request would build an unroutable /en-us/ prefix
        translation.activate('en')
        self.addCleanup(translation.deactivate)
        self.room = Room.objects.create(name='Lobby')
        self.alice = User.objects.create_user('alice', password='pw')
        self.bob = User.objects.create_user('bob', password='pw')
        self.staff = User.objects.create_user('mod', password='pw', is_staff=True)
        self.outsider = User.objects.create_user('eve', password='pw')
        for user in (self.alice, self.bob, self.staff):
            Membership.objects.create(user=user, room=self.room)
        self.url = reverse('room_messages', args=[self.room.id])

    def poll(self, user, since):
        self.client.force_login(user)
        return self.client.get(self.url, {'since': since.isoformat()})

    def ids(self, response):
        return [m['id'] for m in response.json()['messages']]


class RoomMessagesGetTests(PollingTestCase):
    def test_requires_login(self):
        response = self.client.get(self.url, {'since': timezone.now().isoformat()})
        self.assertEqual(response.status_code, 302)

    def test_non_member_forbidden(self):
        response = self.poll(self.outsider, timezone.now())
        self.assertEqual(response.status_code, 403)

    def test_invalid_since_rejected(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(self.url).status_code, 400)
        self.assertEqual(self.client.get(self.url, {'since': 'yesterday'}).status_code, 400)

    def test_returns_messages_after_cursor_only(self):
        old = Message.objects.create(room=self.room, author=self.bob, content='old', approved=True)
        Message.objects.filter(id=old.id).update(
            created_at=timezone.now() - timedelta(minutes=5),
            updated_at=timezone.now() - timedelta(minutes=5),
        )
        cursor = timezone.now()
        new = Message.objects.create(room=self.room, author=self.bob, content='new', approved=True)

        response = self.poll(self.alice, cursor)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.ids(response), [new.id])
        payload = response.json()['messages'][0]
        self.assertEqual(payload['author'], 'bob')
        self.assertTrue(payload['approved'])
        self.assertIn('cursor', response.json())

    def test_overlap_window_includes_recent_rows(self):
        cursor = timezone.now()
        message = Message.objects.create(room=self.room, author=self.bob, content='late commit', approved=True)
        Message.objects.filter(id=message.id).update(updated_at=cursor - POLL_OVERLAP / 2)

        self.assertEqual(self.ids(self.poll(self.alice, cursor)), [message.id])

    def test_unapproved_hidden_from_other_members(self):
        cursor = timezone.now() - timedelta(seconds=30)
        pending = Message.objects.create(room=self.room, author=self.bob, content='pending', approved=False)

        response = self.poll(self.alice, cursor)

        self.assertEqual(self.ids(response), [])
        self.assertIn(pending.id, response.json()['deleted'])

    def test_unapproved_visible_to_author_and_staff(self):
        cursor = timezone.now() - timedelta(seconds=30)
        pending = Message.objects.create(room=self.room, author=self.bob, content='pending', approved=False)

        self.assertEqual(self.ids(self.poll(self.bob, cursor)), [pending.id])
        self.assertEqual(self.ids(self.poll(self.staff, cursor)), [pending.id])

    def test_approval_reaches_other_members(self):
        pending = Message.objects.create(room=self.room, author=self.bob, content='pending', approved=False)
        cursor = timezone.now() + POLL_OVERLAP  # well past creation, outside the overlap
        self.client.force_login(self.staff)
        self.client.post(reverse('approve_message', args=[pending.id]))
        Message.objects.filter(id=pending.id).update(updated_at=cursor + timedelta(seconds=1))

        response = self.poll(self.alice, cursor)

        self.assertEqual(self.ids(response), [pending.id])
        self.assertTrue(response.json()['messages'][0]['approved'])

    def test_deletion_reported_to_other_members(self):
        message = Message.objects.create(room=self.room, author=self.bob, content='bye', approved=True)
        cursor = timezone.now() - timedelta(seconds=30)
        self.client.force_login(self.bob)
        self.client.post(reverse('delete_message', args=[message.id]))

        response = self.poll(self.alice, cursor)

        self.assertEqual(response.json()['deleted'], [message.id])
        self.assertEqual(self.ids(response), [])

    def test_deletions_in_other_rooms_not_reported(self):
        other = Room.objects.create(name='Other')
        message = Message.objects.create(room=other, author=self.bob, content='elsewhere', approved=True)
        cursor = timezone.now() - timedelta(seconds=30)
        message.delete()

        self.assertEqual(self.poll(self.alice, cursor).json()['deleted'], [])

    def test_admin_bulk_approve_bumps_updated_at(self):
        from chat.admin import approve_messages

        pending = Message.objects.create(room=self.room, author=self.bob, content='pending', approved=False)
        before = Message.objects.get(id=pending.id).updated_at

        class FakeAdmin:
            def message_user(self, request, msg):
                pass

        approve_messages(FakeAdmin(), None, Message.objects.filter(id=pending.id))

        self.assertGreater(Message.objects.get(id=pending.id).updated_at, before)

    def test_polling_does_not_touch_last_interaction(self):
        Profile.objects.filter(user=self.alice).update(last_interaction=None)
        self.poll(self.alice, timezone.now())
        self.assertIsNone(Profile.objects.get(user=self.alice).last_interaction)


class RoomMessagesPostTests(PollingTestCase):
    def test_creates_message(self):
        self.client.force_login(self.alice)
        response = self.client.post(self.url, {'content': '<p>hi</p>'})

        self.assertEqual(response.status_code, 201)
        message = Message.objects.get()
        self.assertEqual(response.json()['message']['id'], message.id)
        self.assertEqual(message.author, self.alice)
        self.assertFalse(message.approved)

    def test_auto_approve_profile(self):
        Profile.objects.filter(user=self.alice).update(auto_approve=True)
        self.client.force_login(self.alice)
        self.client.post(self.url, {'content': '<p>hi</p>'})
        self.assertTrue(Message.objects.get().approved)

    def test_empty_message_rejected(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(self.url, {'content': '   '}).status_code, 400)
        self.assertFalse(Message.objects.exists())

    def test_non_member_cannot_post(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(self.url, {'content': 'x'}).status_code, 403)
        self.assertFalse(Message.objects.exists())

    def test_requires_csrf_token(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        self.assertEqual(client.post(self.url, {'content': 'x'}).status_code, 403)

    def test_links_uploaded_images(self):
        image = Image.objects.create(data=b'x', filename='a.png', content_type='image/png')
        self.client.force_login(self.alice)
        self.client.post(self.url, {'content': f'<img src="/image/{image.id}/">'})
        image.refresh_from_db()
        self.assertEqual(image.message, Message.objects.get())

    def test_last_interaction_updated_on_send(self):
        Profile.objects.filter(user=self.alice).update(last_interaction=None)
        self.client.force_login(self.alice)
        self.client.post(self.url, {'content': 'x'})
        self.assertIsNotNone(Profile.objects.get(user=self.alice).last_interaction)


class RoomPageTests(PollingTestCase):
    def test_form_fallback_still_posts(self):
        self.client.force_login(self.alice)
        response = self.client.post(reverse('room', args=[self.room.id]), {'content': 'no js'})
        self.assertRedirects(response, reverse('room', args=[self.room.id]))
        self.assertEqual(Message.objects.get().content, 'no js')

    def test_page_renders_localised_urls(self):
        self.client.force_login(self.alice)
        response = self.client.get(f'/de/room/{self.room.id}/')
        self.assertContains(response, f'/de/room/{self.room.id}/messages/')
        self.assertContains(response, '/de/message/0/delete/')
        self.assertContains(response, 'id="poll-cursor"')

    def test_unapproved_not_rendered_for_others(self):
        Message.objects.create(room=self.room, author=self.bob, content='secret-pending', approved=False)
        self.client.force_login(self.alice)
        response = self.client.get(reverse('room', args=[self.room.id]))
        self.assertNotContains(response, 'secret-pending')


class TombstoneTests(PollingTestCase):
    def test_room_delete_cascade_leaves_tombstones(self):
        message = Message.objects.create(room=self.room, author=self.bob, content='x', approved=True)
        self.room.delete()
        self.assertTrue(DeletedMessage.objects.filter(message_id=message.id).exists())

    def test_old_tombstones_pruned_on_new_message(self):
        stale = DeletedMessage.objects.create(message_id=1, room_id=self.room.id)
        DeletedMessage.objects.filter(id=stale.id).update(deleted_at=timezone.now() - timedelta(days=2))
        Message.objects.create(room=self.room, author=self.bob, content='x')
        self.assertFalse(DeletedMessage.objects.filter(id=stale.id).exists())


@override_settings(MAX_UPLOAD_BYTES=10)
class UploadTests(PollingTestCase):
    url_name = 'upload_image'

    def upload(self, data=b'12345', content_type='image/png'):
        return self.client.post(reverse(self.url_name), {
            'upload': SimpleUploadedFile('a.png', data, content_type=content_type),
        })

    def test_requires_login(self):
        self.assertEqual(self.upload().status_code, 302)
        self.assertFalse(Image.objects.exists())

    def test_upload_returns_url(self):
        self.client.force_login(self.alice)
        response = self.upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['url'], f'/image/{Image.objects.get().id}/')

    def test_too_large_rejected(self):
        self.client.force_login(self.alice)
        response = self.upload(data=b'x' * 11)
        self.assertEqual(response.status_code, 413)
        self.assertIn('message', response.json()['error'])
        self.assertFalse(Image.objects.exists())

    def test_non_image_rejected(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.upload(content_type='text/html').status_code, 400)
        self.assertFalse(Image.objects.exists())

    def test_get_not_allowed(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse(self.url_name)).status_code, 405)


class CkeditorUploadTests(UploadTests):
    url_name = 'ckeditor_upload'
