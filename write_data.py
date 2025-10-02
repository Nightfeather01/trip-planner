from models import PlaceTypes, CityInfosMapping, Keywords
from extensions import db
from sqlalchemy import text


def add_place_types():

    place_types = [
        PlaceTypes(t_id=1, t_name='bar'),
        PlaceTypes(t_id=2, t_name='cafe'),
        PlaceTypes(t_id=3, t_name='museum'),
        PlaceTypes(t_id=4, t_name='park'),
        PlaceTypes(t_id=5, t_name='shopping_mall'),
        PlaceTypes(t_id=6, t_name='zoo'),
        PlaceTypes(t_id=7, t_name='tourist_attraction'),
        PlaceTypes(t_id=8, t_name='restaurant')
    ]

    try:
        for place_type in place_types:
            db.session.add(place_type)

        db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()


def add_city_infos():

    city_infos = [
        CityInfosMapping(c_english='taipei', c_chinese='臺北市', radius=8000, lat=25.0330, lng=121.5654,
                        postal_code_min=100, postal_code_max=117, city_hall_lat=25.03746, city_hall_lng=121.56383),
        CityInfosMapping(c_english='newtaipei', c_chinese='新北市', radius=15000, lat=25.0120, lng=121.4657,
                         postal_code_min=207, postal_code_max=253, city_hall_lat=25.01229, city_hall_lng=121.46554),
        CityInfosMapping(c_english='taoyuan', c_chinese='桃園市', radius=12000, lat=24.9936, lng=121.3010,
                         postal_code_min=320, postal_code_max=339, city_hall_lat=24.99290, city_hall_lng=121.30106),
        CityInfosMapping(c_english='taichung', c_chinese='臺中市', radius=12000, lat=24.1477, lng=120.6736,
                         postal_code_min=400, postal_code_max=439, city_hall_lat=24.16188, city_hall_lng=120.64685),
        CityInfosMapping(c_english='tainan', c_chinese='臺南市', radius=12000, lat=22.9999, lng=120.2268,
                         postal_code_min=700, postal_code_max=745, city_hall_lat=22.99242, city_hall_lng=120.18506),
        CityInfosMapping(c_english='kaohsiung', c_chinese='高雄市', radius=15000, lat=22.6273, lng=120.3014,
                         postal_code_min=800, postal_code_max=852, city_hall_lat=22.62049, city_hall_lng=120.31206),
        CityInfosMapping(c_english='keelung', c_chinese='基隆市', radius=5000, lat=25.1276, lng=121.7392,
                        postal_code_min=200, postal_code_max=206, city_hall_lat=25.13181, city_hall_lng=121.74446),
        CityInfosMapping(c_english='hsinchu_city', c_chinese='新竹市', radius=5000, lat=24.8138, lng=120.9675,
                        postal_code_min=300, postal_code_max=300, city_hall_lat=24.80674, city_hall_lng=120.96889),
        CityInfosMapping(c_english='hsinchu', c_chinese='新竹縣', radius=10000, lat=24.8397, lng=121.0196,
                        postal_code_min=302, postal_code_max=315, city_hall_lat=24.82704, city_hall_lng=121.01280),
        CityInfosMapping(c_english='miaoli', c_chinese='苗栗縣', radius=10000, lat=24.5602, lng=120.8214,
                        postal_code_min=350, postal_code_max=369, city_hall_lat=24.56490, city_hall_lng=120.82070),
        CityInfosMapping(c_english='changhua', c_chinese='彰化縣', radius=10000, lat=24.0518, lng=120.5161,
                        postal_code_min=500, postal_code_max=530, city_hall_lat=24.07557, city_hall_lng=120.54451),
        CityInfosMapping(c_english='nantou', c_chinese='南投縣', radius=15000, lat=23.9609, lng=120.9718,
                        postal_code_min=540, postal_code_max=558, city_hall_lat=23.90270, city_hall_lng=120.69054),
        CityInfosMapping(c_english='yunlin', c_chinese='雲林縣', radius=10000, lat=23.7092, lng=120.4313,
                         postal_code_min=630, postal_code_max=655, city_hall_lat=23.69949, city_hall_lng=120.52640),
        CityInfosMapping(c_english='chiayi_city', c_chinese='嘉義市', radius=5000, lat=23.4801, lng=120.4490,
                        postal_code_min=600, postal_code_max=600, city_hall_lat=23.48129, city_hall_lng=120.45360),
        CityInfosMapping(c_english='chiayi', c_chinese='嘉義縣', radius=10000, lat=23.4518, lng=120.2555,
                        postal_code_min=602, postal_code_max=625, city_hall_lat=23.46043, city_hall_lng=120.29229),
        CityInfosMapping(c_english='pingtung', c_chinese='屏東縣', radius=12000, lat=22.5519, lng=120.5487,
                        postal_code_min=900, postal_code_max=947, city_hall_lat=22.68320, city_hall_lng=120.48789),
        CityInfosMapping(c_english='yilan', c_chinese='宜蘭縣', radius=10000, lat=24.7021, lng=121.7377,
                         postal_code_min=260, postal_code_max=290, city_hall_lat=24.73093, city_hall_lng=121.76311),
        CityInfosMapping(c_english='hualien', c_chinese='花蓮縣', radius=15000, lat=23.9871, lng=121.6011,
                         postal_code_min=970, postal_code_max=983, city_hall_lat=23.99169, city_hall_lng=121.61988),
        CityInfosMapping(c_english='taitung', c_chinese='臺東縣', radius=15000, lat=22.7583, lng=121.1444,
                        postal_code_min=950, postal_code_max=966, city_hall_lat=22.75564, city_hall_lng=121.15035),
        CityInfosMapping(c_english='penghu', c_chinese='澎湖縣', radius=8000, lat=23.5711, lng=119.5793,
                        postal_code_min=880, postal_code_max=885, city_hall_lat=23.57010, city_hall_lng=119.56636),
        CityInfosMapping(c_english='kinmen', c_chinese='金門縣', radius=5000, lat=24.4486, lng=118.3186,
                        postal_code_min=890, postal_code_max=896, city_hall_lat=24.43691, city_hall_lng=118.31887),
        CityInfosMapping(c_english='lienchiang', c_chinese='連江縣', radius=5000, lat=26.1505, lng=119.9528,
                        postal_code_min=209, postal_code_max=212, city_hall_lat=26.15808, city_hall_lng=119.95202)
    ]

    try:
        for city in city_infos:
            stmt = (
                db.session.query(CityInfosMapping)
                .filter(CityInfosMapping.c_english == city.c_english)
                .one_or_none()
            )

            if stmt:
                # 更新現有記錄
                stmt.c_chinese = city.c_chinese
                stmt.radius = city.radius
                stmt.lat = city.lat
                stmt.lng = city.lng
                stmt.postal_code_min = city.postal_code_min
                stmt.postal_code_max = city.postal_code_max
                stmt.city_hall_lat = city.city_hall_lat
                stmt.city_hall_lng = city.city_hall_lng
            else:
                # 插入新記錄
                db.session.add(city)

        db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()


def add_keywords():
    # 先清空現有的 keywords 表
    try:
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=0'))
        db.session.query(Keywords).delete()
        db.session.execute(text('ALTER TABLE keywords AUTO_INCREMENT = 1'))
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
        db.session.commit()
    except Exception as e:
        print(f"Error clearing keywords table: {e}")
        db.session.rollback()
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
        return

    types_keywords = [
        Keywords(k_id=1, k_name='酒吧', place_types=1),
        Keywords(k_id=2, k_name='咖啡廳', place_types=2),
        Keywords(k_id=3, k_name='博物館', place_types=3),
        Keywords(k_id=4, k_name='公園', place_types=4),
        Keywords(k_id=5, k_name='百貨公司', place_types=5),
        Keywords(k_id=6, k_name='動物園', place_types=6),
        Keywords(k_id=7, k_name='觀光景點', place_types=7),
        Keywords(k_id=8, k_name='餐廳', place_types=8)
    ]

    food_keywords = [
        "火雞肉飯", "肉圓", "臭豆腐", "滷肉飯", "牛肉麵", "燒烤",
        "蚵仔煎", "擔仔麵", "蝦捲", "虱目魚", "生魚片", "水餃",
        "小籠包", "雞排", "珍珠奶茶", "魯肉飯", "蔥油餅", "鹽酥雞",
        "大腸包小腸", "豆花", "米粉", "肉粽", "蜜餞", "豬血糕"
    ]

    attraction_keywords = [
        "親子活動", "生態園區", "文化園區", "自行車道", "藝術園區",
        "漁港", "老街", "夜市", "花市", "瀑布", "溫泉", "農場",
        "草原", "海灘", "濕地", "古蹟", "廟宇", "登山步道",
        "觀景台", "森林遊樂區", "茶園", "原住民部落", "燈塔",
        "紀念館", "展覽館", "植物園"  # 移除了'博物館'和'動物園'，因為已在types_keywords中
    ]

    try:
        # 先插入 types_keywords
        for keyword in types_keywords:
            try:
                db.session.merge(keyword)
                db.session.flush()
            except Exception as e:
                print(f"Error adding type keyword {keyword.k_name}: {e}")
                continue

        # 獲取restaurant和tourist_attraction的t_id
        restaurant_type = db.session.query(PlaceTypes).filter(PlaceTypes.t_name == 'restaurant').first()
        tourist_type = db.session.query(PlaceTypes).filter(PlaceTypes.t_name == 'tourist_attraction').first()

        if not restaurant_type or not tourist_type:
            print("Error: Required place types not found")
            return

        # 添加食物關鍵字
        for keyword in food_keywords:
            try:
                existing = db.session.query(Keywords).filter(Keywords.k_name == keyword).first()
                if not existing:
                    new_keyword = Keywords(k_name=keyword, place_types=restaurant_type.t_id)
                    db.session.add(new_keyword)
                    db.session.flush()
            except Exception as e:
                print(f"Error adding food keyword {keyword}: {e}")
                continue

        # 添加景點關鍵字
        for keyword in attraction_keywords:
            try:
                existing = db.session.query(Keywords).filter(Keywords.k_name == keyword).first()
                if not existing:
                    new_keyword = Keywords(k_name=keyword, place_types=tourist_type.t_id)
                    db.session.add(new_keyword)
                    db.session.flush()
            except Exception as e:
                print(f"Error adding attraction keyword {keyword}: {e}")
                continue

        db.session.commit()
    except Exception as e:
        print(f"Error adding keywords: {e}")
        db.session.rollback()
