from flask import g
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from sqlalchemy.orm import aliased
from extensions import db, session
from models import UserInfos, Preference, UserInfosPreference, Journey


def add_user(form):
    account = form.account.data
    disabilities = form.disabilities.data
    password = form.password.data
    email = form.email.data
    id_card = form.id_card.data
    phone_number = form.phone_number.data
    real_name = form.real_name.data
    address = form.address.data
    birthday = form.birthday.data
    user = UserInfos(
        account=account,
        disabilities=disabilities,
        password=generate_password_hash(password),
        email=email,
        id_card=generate_password_hash(id_card),
        phone_number=phone_number,
        real_name=real_name,
        address=address,
        birthday=birthday)
    db.session.add(user)
    db.session.commit()


def add_or_edit_preference(form):
    p_name = form.p_name.data
    esp_dep = form.esp_dep.data
    esp_ret = form.esp_ret.data
    dep_day = form.dep_day.data
    ret_day = form.ret_day.data
    budget = form.budget.data
    traffic_mode_round_trip = form.traffic_mode_round_trip.data
    traffic_mode_local = form.traffic_mode_local.data
    travel_mode = form.travel_mode.data
    if form.p_id.data:
        preference = Preference(
            p_id=form.p_id.data,
            p_name=p_name,
            esp_dep=esp_dep,
            esp_ret=esp_ret,
            dep_day=dep_day,
            ret_day=ret_day,
            budget=budget,
            traffic_mode_round_trip=traffic_mode_round_trip,
            traffic_mode_local=traffic_mode_local,
            travel_mode=travel_mode
        )
        db.session.update(preference)
    else:
        preference = Preference(
            p_name=p_name,
            esp_dep=esp_dep,
            esp_ret=esp_ret,
            dep_day=dep_day,
            ret_day=ret_day,
            budget=budget,
            traffic_mode_round_trip=traffic_mode_round_trip,
            traffic_mode_local=traffic_mode_local,
            travel_mode=travel_mode
        )
        db.session.add(preference)
    db.session.commit()


UserInfosPreference1 = aliased(UserInfosPreference)
UserInfosPreference2 = aliased(UserInfosPreference)


def search_preferences_and_journeys():
    user_preferences = (session.query(
        UserInfos.u_id,
        UserInfos.account,
        Preference.p_id,
        Preference.p_name,
        func.count(UserInfosPreference1.u_id).label('user_count'),
        func.group_concat(UserInfosPreference1.u_id).label('user_ids')
    )
                        .join(UserInfosPreference1, UserInfos.u_id == UserInfosPreference1.u_id)
                        .join(Preference, Preference.p_id == UserInfosPreference1.p_id)
                        .filter(UserInfos.u_id == g.user)
                        .group_by(Preference.p_id)
                        .all())
    preferences_with_journeys = []
    for pref in user_preferences:
        journeys = session.query(Journey.j_id, Journey.j_name).filter_by(p_id=pref.p_id).all()
        preferences_with_journeys.append({
            'preference': pref,
            'journeys': journeys
        })

    return preferences_with_journeys
