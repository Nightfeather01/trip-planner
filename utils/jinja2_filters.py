# 在trip_plan.py中的imports部分添加
from markupsafe import Markup  # 修改這一行


def init_jinja2_filters(app):
    """初始化Jinja2過濾器"""

    @app.template_filter('generate_stars')
    def generate_stars(rating):
        """生成評分星星HTML"""
        full_stars = int(rating)
        has_half_star = (rating % 1) >= 0.5
        html = []

        for i in range(5):
            if i < full_stars:
                html.append('<i class="bi bi-star-fill text-warning"></i>')
            elif i == full_stars and has_half_star:
                html.append('<i class="bi bi-star-half text-warning"></i>')
            else:
                html.append('<i class="bi bi-star text-warning"></i>')

        return Markup(''.join(html))

    @app.template_filter('generate_price')
    def generate_price(level):
        """生成價格等級HTML"""
        level = int(level) + 1  # 將0-4轉換為1-5
        html = []

        for i in range(5):
            if i < level:
                html.append('<i class="bi bi-currency-dollar text-success"></i>')
            else:
                html.append('<i class="bi bi-currency-dollar text-muted"></i>')

        return Markup(''.join(html))

    @app.template_filter('filter_by_type')
    def filter_by_type(places, place_type):
        return [place for place in places if place_type in place['types']]

    @app.template_filter('filter_by_rating')
    def filter_by_rating(places, min_rating=4.5):
        return [place for place in places if place['rating'] >= min_rating]

    @app.template_filter('filter_by_price')
    def filter_by_price(places, max_price=1):
        return [place for place in places if place['price_level'] <= max_price]

    @app.template_filter('sort_by_rating')
    def sort_by_rating(places):
        return sorted(places, key=lambda x: x['rating'], reverse=True)

    @app.template_filter('sort_by_reviews')
    def sort_by_reviews(places):
        return sorted(places, key=lambda x: x['user_rating_totals'], reverse=True)