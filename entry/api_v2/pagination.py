from rest_framework.pagination import LimitOffsetPagination

from entry.settings import CONFIG


class EntryReferralPagination(LimitOffsetPagination):
    max_limit = CONFIG.MAX_LIST_REFERRALS
