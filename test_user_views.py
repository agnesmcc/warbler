"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


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


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        db.session.commit()

        self.testmsg1 = Message(text="Test message 1", user_id=self.testuser.id)
        self.testmsg2 = Message(text="Test message 2", user_id=self.testuser2.id)
        db.session.add_all([self.testmsg1, self.testmsg2])
        db.session.commit()

    def test_user_signup(self):
        """Can user sign up?"""
        with self.client as c:
            resp = c.post("/signup", data={"username": "testuser3",
                                            "password": "testuser3",
                                            "email": "test3@test.com",
                                            "image_url": None})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(User.query.count(), 3)

    def test_list_users(self):
        """Can user list users?"""
        with self.client as c:
            resp = c.get("/users")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser", resp.data)
            self.assertIn(b"testuser2", resp.data)

    def test_user_show_profile(self):
        """Can user show profile?"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser", resp.data)

    def test_user_add_follow(self):
        """Can user add follow?"""
        testuser2_id = self.testuser2.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/follow/{testuser2_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser2", resp.data)

    def test_user_unfollow(self):
        """Can user unfollow?"""
        testuser2_id = self.testuser2.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/follow/{testuser2_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser2", resp.data)

            resp = c.post(f"/users/stop-following/{testuser2_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(b"testuser2", resp.data)

    def test_user_delete(self):
        """Can user delete themselves?"""

        testuser1_id = self.testuser.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(User.query.get(testuser1_id), None)
            
    def test_user_edit_profile(self):
        """Can user edit their profile?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/profile")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser", resp.data)

            resp = c.post(f"/users/profile", 
                data={"username": "testuser3",
                     "password": "testuser", # This is the user's password not a new one
                     "email": "test3@test.com",
                     "image_url": None}, 
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(User.query.count(), 2)
            self.assertIn(b"testuser3", resp.data)

    def test_user_add_like(self):
        """Can user like another user's message?"""
        testmsg2_id = self.testmsg2.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/add_like/{testmsg2_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            testuser = User.query.get(self.testuser.id)
            self.assertIn(testmsg2_id, [m.id for m in testuser.likes])

            resp = c.post(f"/users/add_like/{testmsg2_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            testuser = User.query.get(self.testuser.id)
            self.assertNotIn(testmsg2_id, [m.id for m in testuser.likes])
