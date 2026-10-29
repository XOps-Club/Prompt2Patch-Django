from django.db import models


class Link(models.Model):
    original_url = models.CharField(max_length=2048)
    short_code = models.CharField(max_length=64, db_index=True)
    clicks = models.PositiveIntegerField(default=0)
    unique_clicks = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['short_code'],
                condition=models.Q(is_deleted=False),
                name='unique_active_link_short_code',
            ),
        ]

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"

    @property
    def conversion_rate(self) -> float:
        if self.clicks == 0:
            return 0.0
        return round((self.unique_clicks / self.clicks) * 100, 2)

    def get_top_referrer(self) -> str:
        top = (
            self.click_logs.values('referrer')
            .annotate(total=models.Count('id'))
            .order_by('-total')
            .first()
        )
        return top['referrer'] if top else 'direct'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'original_url': self.original_url,
            'short_code': self.short_code,
            'clicks': self.clicks,
            'unique_clicks': self.unique_clicks,
            'conversion_rate': self.conversion_rate,
            'top_referrer': self.get_top_referrer(),
            'is_deleted': 1 if self.is_deleted else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ClickLog(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='click_logs')
    referrer = models.CharField(max_length=255, default='direct')
    user_agent = models.TextField(blank=True, default='')
    ip_hash = models.CharField(max_length=64, default='unknown', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Click for {self.link.short_code} from {self.referrer}"
