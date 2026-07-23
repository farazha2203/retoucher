from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import EditorProfile
from customer_membership.ranking import calculate_editor_score


class RankingTests(TestCase):
    def test_editor_score_increases_with_rating(self):
        User = get_user_model()
        low_user = User.objects.create_user(username="low", role="editor")
        high_user = User.objects.create_user(username="high", role="editor")
        low = EditorProfile.objects.create(user=low_user, rating_average=5)
        high = EditorProfile.objects.create(user=high_user, rating_average=9)
        self.assertGreater(
            calculate_editor_score(high),
            calculate_editor_score(low),
        )
