"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message(self):
        """Can user delete a message?"""

        m = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        msg_id = m.id # To avoid DetachedInstanceError http://sqlalche.me/e/bhk3

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{msg_id}/delete")

            self.assertEqual(resp.status_code, 302)

            m = Message.query.get(m.id)
            self.assertIsNone(m)

    def test_logged_out_users_cannot_delete_messages(self):
        """Can logged out users delete messages?"""

        m = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        msg_id = m.id # To avoid DetachedInstanceError http://sqlalche.me/e/bhk3

        with self.client as c:
            resp = c.post(f"/messages/{msg_id}/delete")

            self.assertEqual(resp.status_code, 302)
            m = Message.query.get(msg_id)
            self.assertIsNotNone(m)
    
    def test_looged_out_users_cannot_add_messages(self):
        """Can logged out users add messages?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one_or_none()
            self.assertIsNone(msg)
    
    def test_logged_in_user_cannot_delete_another_users_messages(self):
        """Can logged in user delete another user's messages?"""

        m = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        msg_id = m.id # To avoid DetachedInstanceError http://sqlalche.me/e/bhk3

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id + 1

            resp = c.post(f"/messages/{msg_id}/delete")

            self.assertEqual(resp.status_code, 302)
            m = Message.query.get(msg_id)
            self.assertIsNotNone(m)
