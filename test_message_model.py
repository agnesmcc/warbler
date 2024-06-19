"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError, DataError

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


class MessageModelTestCase(TestCase):
    """Test message model."""

    
    def tearDown(self):
        """Clean up after each test."""
        try:
            db.session.rollback()
        except InvalidRequestError:
            pass
        finally:
            db.session.close()

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

    def test_create_message(self):
        """Does the message model create new messages?"""

        m5 = Message(text="Test message 5", user_id=self.testuser.id)

        db.session.add(m5)
        db.session.commit()

        self.assertEqual(m5.user_id, self.testuser.id)

    def test_create_message_with_invalid_user(self):
        """Does the message model fail to create new messages with an invalid user?"""

        m5 = Message(text="Test message 5", user_id=1000)

        with self.assertRaises(IntegrityError):
            db.session.add(m5)
            db.session.commit()

        db.session.rollback()

    def test_create_message_fail_with_long_text(self):
        """Does the message model fail to create new messages with a long text?"""

        m5 = Message(text="a" * 1000, user_id=self.testuser.id)

        with self.assertRaises(DataError):
            db.session.add(m5)
            db.session.commit()

        db.session.rollback()