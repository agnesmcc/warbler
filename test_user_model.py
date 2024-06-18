"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test",
                                     password="testuser2",
                                     image_url=None)
        
        db.session.add_all([self.testuser, self.testuser2])
        db.session.commit()

        self.m1 = Message(text="Test message 1", user_id=self.testuser.id)
        self.m2 = Message(text="Test message 2", user_id=self.testuser.id)
        self.m3 = Message(text="Test message 3", user_id=self.testuser2.id)
        self.m4 = Message(text="Test message 4", user_id=self.testuser2.id)

        db.session.add_all([self.m1, self.m2, self.m3, self.m4])
        db.session.commit()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the repr method work?"""

        self.assertEqual(repr(self.testuser), 
            f"<User #{self.testuser.id}: {self.testuser.username}, {self.testuser.email}>")
        self.assertEqual(repr(self.testuser2), 
            f"<User #{self.testuser2.id}: {self.testuser2.username}, {self.testuser2.email}>")