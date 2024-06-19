"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

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

    def test_following(self):
        """Does is_following detect when a user is following another user?"""
        self.testuser.following.append(self.testuser2)
        db.session.commit()
        self.assertTrue(self.testuser.is_following(self.testuser2))

    def test_not_following(self):
        """Does is_following detect when a user is not following another user?"""
        self.assertFalse(self.testuser2.is_following(self.testuser))

    def test_is_followed_by(self):
        """Does is_followed_by detect when a user is followed by another user?"""
        self.testuser.following.append(self.testuser2)
        db.session.commit()
        self.assertTrue(self.testuser2.is_followed_by(self.testuser))

    def test_not_is_followed_by(self):
        """Does is_followed_by detect when a user is not followed by another user?"""
        self.assertFalse(self.testuser.is_followed_by(self.testuser2))


    def test_failed_creation(self):
        """Does user creation fail with bad data?"""

        first_user = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD"
        )

        db.session.add(first_user)
        db.session.commit()

        # test that a duplicate user cannot be created
        duplicate_user = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD"
        )

        with self.assertRaises(IntegrityError):
            db.session.add(duplicate_user)
            db.session.commit()

        db.session.rollback()    
    
        # test that a user cannot be created with a null password
        with self.assertRaises(IntegrityError):
            db.session.add(User(
                email="test4@test.com",
                username="testuser4",
                password=None
            ))
            db.session.commit()

    def test_user_authenticate_success(self):
        """Does user authentication work?"""
        user = User.authenticate(self.testuser.username, "testuser")
        self.assertEqual(user, self.testuser)

    def test_user_authenticate_fail_invalid_username(self):
        """Does user authentication fail with invalid username?"""
        user = User.authenticate("testuser3", "testuser")
        self.assertFalse(user)
    
    def test_user_authenticate_fail_invalid_password(self):
        """Does user authentication fail with invalid password?"""
        user = User.authenticate(self.testuser.username, "testuser3")
        self.assertFalse(user)
