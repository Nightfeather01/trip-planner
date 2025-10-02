from extensions import db
from datetime import datetime
import uuid


class UserInfos(db.Model):

    __tablename__ = 'user_infos'
    table_args = {'extend_existing': True}
    u_id = db.Column(db.UUID, default=uuid.uuid4, unique=True, nullable=False, primary_key=True)
    disabilities = db.Column(db.Boolean, default=False, nullable=True)
    account = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=True)
    u_join_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    id_card = db.Column(db.String(255), unique=True, nullable=True)
    phone_number = db.Column(db.String(10), unique=True, nullable=True)
    real_name = db.Column(db.String(24), nullable=True)
    address = db.Column(db.String(60), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    # relation to preference(many to many)
    preferences = db.relationship('Preference', secondary='user_infos_preference', backref='user_infos')
    # relation to journey(many to many)
    journeys = db.relationship('Journey', secondary='user_infos_journey', backref='user_infos')


class Preference(db.Model):

    __tablename__ = 'preference'
    table_args = {'extend_existing': True}
    p_id = db.Column(db.UUID, default=uuid.uuid4, unique=True, nullable=False, primary_key=True)
    p_join_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    p_name = db.Column(db.String(255), default='新增旅行喜好', nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    return_datetime = db.Column(db.DateTime, nullable=False)
    daily_depart_time = db.Column(db.Time, nullable=False)
    daily_return_time = db.Column(db.Time, nullable=False)
    budget = db.Column(db.SmallInteger, nullable=False)
    travel_mode = db.Column(db.Boolean, nullable=False)
    price_level_weight = db.Column(db.Float, nullable=False)
    rating_weight = db.Column(db.Float, nullable=False)
    user_rating_total_weight = db.Column(db.Float, nullable=False)
    # TODO: add customize traffic mode preference
    # traffic_mode_round_trip = db.Column(db.SmallInteger, nullable=False)
    # traffic_mode_local = db.Column(db.SmallInteger, nullable=False)
    # relation to keywords(many to many)
    keywords = db.relationship('Keywords', secondary='preference_keywords', backref='preferences')
    # relation to city_infos_mapping(many to one)
    city = db.Column(db.Integer, db.ForeignKey('city_infos_mapping.c_id'), nullable=False)


class Journey(db.Model):

    __tablename__ = 'journey'
    table_args = {'extend_existing': True}
    j_id = db.Column(db.UUID, default=uuid.uuid4, unique=True, nullable=False, primary_key=True)
    j_join_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    j_name = db.Column(db.String(255), default='新增旅行計畫', nullable=False)
    j_departure_datetime = db.Column(db.DateTime, nullable=False)
    j_return_datetime = db.Column(db.DateTime, nullable=False)
    j_budget = db.Column(db.SmallInteger, nullable=False)
    # relation to keywords(many to many)
    keywords = db.relationship('Keywords', secondary='journey_keywords_snapshot', backref='journey')
    # relation to city_infos_mapping(many to one)
    city = db.Column(db.Integer, db.ForeignKey('city_infos_mapping.c_id'), nullable=False)
    # relation to preference(many to one)
    preference = db.Column(db.UUID, db.ForeignKey('preference.p_id'), nullable=False)


class PlaceInfos(db.Model):

    __tablename__ = 'place_infos'
    table_args = {'extend_existing': True}
    place_id = db.Column(db.String(255), nullable=False, unique=True, primary_key=True)
    place_last_updated = db.Column(db.DateTime, default=datetime.now, nullable=False)
    place_lat = db.Column(db.Float, nullable=False)
    place_lng = db.Column(db.Float, nullable=False)
    place_name = db.Column(db.String(255), nullable=False)
    formatted_address = db.Column(db.Text, nullable=False)
    place_phone_number = db.Column(db.String(20), nullable=True)
    place_price_level = db.Column(db.Integer, nullable=False)
    place_rating = db.Column(db.Float, nullable=False)
    place_rating_total = db.Column(db.Integer, nullable=False)
    place_disabilities_friendly = db.Column(db.Boolean, default=False, nullable=False)
    # relation to place_types(many to many)
    # place_types = db.relationship('PlaceTypes', secondary='place_infos_type', backref='place_infos')
    # relation to keywords(many to many)
    keywords = db.relationship('Keywords', secondary='place_infos_keywords', backref='place_infos')
    # relation to city_infos_mapping(many to one)
    city = db.Column(db.Integer, db.ForeignKey('city_infos_mapping.c_id'), nullable=False)


class PlaceTypes(db.Model):

    __tablename__ = 'place_types'
    table_args = {'extend_existing': True}
    t_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    t_name = db.Column(db.String(255), nullable=False, unique=True)


class Keywords(db.Model):

    __tablename__ = 'keywords'
    table_args = {'extend_existing': True}
    k_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    k_name = db.Column(db.String(255), nullable=False)
    # relation to keywords(many to one)
    place_types = db.Column(db.Integer, db.ForeignKey('place_types.t_id'), nullable=False)


class CityInfosMapping(db.Model):

    __tablename__ = 'city_infos_mapping'
    table_args = {'extend_existing': True}
    c_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    c_english = db.Column(db.String(255), nullable=False, unique=True)
    c_chinese = db.Column(db.String(255), nullable=False, unique=True)
    radius = db.Column(db.Integer, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    postal_code_min = db.Column(db.Integer, nullable=False)
    postal_code_max = db.Column(db.Integer, nullable=False)
    city_hall_lat = db.Column(db.Float, nullable=False)
    city_hall_lng = db.Column(db.Float, nullable=False)


'''
class LodgingPreference(db.Model):

    __tablename__ = 'lodging_preference'

    l_id = db.Column(db.UUID, default=uuid.uuid4, unique=True, nullable=False, primary_key=True)
    guest_qty = db.Column(db.Integer, nullable=False, default=2)
    room_qty = db.Column(db.Integer, nullable=False, default=1)
    min_rating = db.Column(db.Float, nullable=False, default=8.0)
    prefer_facilities = db.Column(db.String(500), nullable=True)
    preference = db.Column(db.UUID, db.ForeignKey('preference.p_id'), nullable=False)


class LodgingResult(db.Model):

    __tablename__ = 'lodging_result'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    hotel_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    review_score = db.Column(db.Float, nullable=True)
    review_count = db.Column(db.Integer, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    booking_url = db.Column(db.String(500), nullable=True)
    preference = db.Column(db.UUID, db.ForeignKey('lodging_preference.l_id'), nullable=False)
'''


class PlacesOfTheJourney(db.Model):

    __tablename__ = 'places_of_the_journey'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    place_start_datetime = db.Column(db.DateTime, nullable=False)
    place_end_datetime = db.Column(db.DateTime, nullable=False)
    # relation to place_infos(many to one)
    place_id = db.Column(db.String(255), db.ForeignKey('place_infos.place_id'), nullable=False)
    # relation to user_journey(many to one)
    journey = db.Column(db.UUID, db.ForeignKey('journey.j_id'), nullable=False)


class PlaceOpeningHoursForEachDays(db.Model):

    __tablename__ = 'place_opening_hours_for_each_days'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    # relation to place_infos(many to one)
    place_id = db.Column(db.String(255), db.ForeignKey('place_infos.place_id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)


class UserInfosPreference(db.Model):

    __tablename__ = 'user_infos_preference'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    u_id = db.Column(db.UUID, db.ForeignKey('user_infos.u_id'), nullable=False)
    p_id = db.Column(db.UUID, db.ForeignKey('preference.p_id'), nullable=False)


class UserInfosJourney(db.Model):

    __tablename__ = 'user_infos_journey'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    u_id = db.Column(db.UUID, db.ForeignKey('user_infos.u_id'), nullable=False)
    j_id = db.Column(db.UUID, db.ForeignKey('journey.j_id'), nullable=False)


class PreferenceKeywords(db.Model):

    __tablename__ = 'preference_keywords'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    p_id = db.Column(db.UUID, db.ForeignKey('preference.p_id'), nullable=False)
    k_id = db.Column(db.Integer, db.ForeignKey('keywords.k_id'), nullable=False)


class JourneyKeywordsSnapshot(db.Model):

    __tablename__ = 'journey_keywords_snapshot'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    j_id = db.Column(db.UUID, db.ForeignKey('journey.j_id'), nullable=False)
    k_id = db.Column(db.Integer, db.ForeignKey('keywords.k_id'), nullable=False)


class PlaceInfosKeywords(db.Model):

    __tablename__ = 'place_infos_keywords'
    table_args = {'extend_existing': True}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    place_id = db.Column(db.String(255), db.ForeignKey('place_infos.place_id'), nullable=False)
    k_id = db.Column(db.Integer, db.ForeignKey('keywords.k_id'), nullable=False)
