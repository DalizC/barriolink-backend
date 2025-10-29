from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework.test import APIRequestFactory, force_authenticate

from core.permissions import IsMemberUser, IsAdminRoleUser, IsOwnerOrAdmin
from core.models import Event

import datetime


class PermissionsTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        User = get_user_model()
        self.member = User.objects.create_user(
            email='member@example.com', password='password', role=User.Role.MEMBER
        )
        self.admin = User.objects.create_user(
            email='admin@example.com', password='password', role=User.Role.ADMIN
        )
        self.registered = User.objects.create_user(
            email='registered@example.com', password='password', role=User.Role.REGISTERED
        )
        self.event_owned_by_member = Event.objects.create(
            user=self.member,
            title='Member Event',
            date=datetime.date.today(),
            duration=datetime.timedelta(hours=1),
            capacity=10,
            location='L1',
            address='A1',
        )
        # another event owned by registered user
        self.event_owned_by_reg = Event.objects.create(
            user=self.registered,
            title='Reg Event',
            date=datetime.date.today(),
            duration=datetime.timedelta(hours=2),
            capacity=5,
            location='L2',
            address='A2',
        )

    def _get_request(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    def test_is_member_user_allows_member_and_admin(self):
        perms = IsMemberUser()
        request_member = self._get_request(self.member)
        self.assertTrue(perms.has_permission(request_member, None))
        request_admin = self._get_request(self.admin)
        self.assertTrue(perms.has_permission(request_admin, None))
    def test_is_member_user_denies_registered_and_anonymous(self):
        perms = IsMemberUser()
        request_registered = self._get_request(self.registered)
        self.assertFalse(perms.has_permission(request_registered, None))
        # anonymous request (sin usuario autenticado)
        anon_request = self._get_request(AnonymousUser())
        self.assertFalse(perms.has_permission(anon_request, None))
    def test_is_admin_role_user_allows_only_admin(self):
        perms = IsAdminRoleUser()
        request_admin = self._get_request(self.admin)
        self.assertTrue(perms.has_permission(request_admin, None))
        request_member = self._get_request(self.member)
        self.assertFalse(perms.has_permission(request_member, None))
    def test_is_owner_or_admin_object_permission(self):
        perms = IsOwnerOrAdmin()
        # member owns event_owned_by_member
        request_member = self._get_request(self.member)
        self.assertTrue(perms.has_object_permission(request_member, None, self.event_owned_by_member))
        # member should not have permission on event owned by reg
        request_member_other = self._get_request(self.member)
        self.assertFalse(perms.has_object_permission(request_member_other, None, self.event_owned_by_reg))
        # admin should have access to either
        request_admin = self._get_request(self.admin)
        self.assertTrue(perms.has_object_permission(request_admin, None, self.event_owned_by_member))
        self.assertTrue(perms.has_object_permission(request_admin, None, self.event_owned_by_reg))
