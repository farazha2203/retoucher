import hashlib
from urllib.parse import parse_qs, urlparse
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import SocialAuthExchangeCode

@override_settings(FRONTEND_AUTH_CALLBACK_URL="http://localhost:3000/auth/callback", SOCIAL_EXCHANGE_CODE_TTL_SECONDS=60)
class GoogleAuthBridgeTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username="google-client@example.com",email="google-client@example.com",password="StrongPass123!",role="client",is_active=True,is_verified=True)
    def create_code(self):
        self.client.force_login(self.user)
        response=self.client.get(reverse("accounts:frontend-auth-bridge"))
        self.assertEqual(response.status_code,302)
        return parse_qs(urlparse(response["Location"]).query)["code"][0]
    def test_exchange_once(self):
        code=self.create_code(); api=APIClient(); url=reverse("accounts:social-auth-exchange")
        response=api.post(url,{"code":code},format="json")
        self.assertEqual(response.status_code,200); self.assertIn("access",response.data); self.assertEqual(response.data["user"]["id"],self.user.id)
        self.assertEqual(api.post(url,{"code":code},format="json").status_code,409)
    def test_raw_code_not_stored(self):
        code=self.create_code(); row=SocialAuthExchangeCode.objects.get()
        self.assertEqual(row.code_digest,hashlib.sha256(code.encode()).hexdigest()); self.assertNotEqual(row.code_digest,code)
    def test_expired_rejected(self):
        code=self.create_code(); SocialAuthExchangeCode.objects.update(expires_at=timezone.now()-timezone.timedelta(seconds=1))
        self.assertEqual(APIClient().post(reverse("accounts:social-auth-exchange"),{"code":code},format="json").status_code,400)
    def test_inactive_rejected(self):
        code=self.create_code(); self.user.is_active=False; self.user.save(update_fields=["is_active"])
        self.assertEqual(APIClient().post(reverse("accounts:social-auth-exchange"),{"code":code},format="json").status_code,403)
