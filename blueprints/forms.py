import wtforms
from wtforms.validators import Email, Length, EqualTo, DataRequired, NumberRange
from models import UserInfos
import requests
from functools import wraps
from flask import request, jsonify
from datetime import datetime, time
import json


# 自定義身分證格式驗證器
class IDCardValidator:
    def __call__(self, form, field):
        pattern = r'^[A-Z][12]\d{8}$'
        if not wtforms.validators.Regexp(pattern)(form, field):
            raise wtforms.ValidationError(message="身分證格式錯誤(開頭須為大寫)")


# 自定義電話號碼格式驗證器
class PhoneNumberValidator:
    def __call__(self, form, field):
        pattern = r'^09\d{8}$'
        if not wtforms.validators.Regexp(pattern)(form, field):
            raise wtforms.ValidationError(message="電話格式錯誤")


# 自定義地址驗證器
class AddressValidator:
    def __call__(self, form, field):
        address = field.data
        api_key = 'AIzaSyDXzV6jMwR7e_bddEjtT7Mgz3pnKHGJacc'
        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'

        response = requests.get(url)
        results = response.json().get('results', [])
        if not results:
            raise wtforms.ValidationError('無效的地址')


# 驗證前端提交的註冊資料是否符合要求
class RegisterForm(wtforms.Form):
    account = wtforms.StringField(validators=[Length(min=4, max=16, message="帳號格式錯誤")])
    disabilities = wtforms.BooleanField("是否為身心障礙者?", validators=[DataRequired(message="此欄位必填")])
    password = wtforms.StringField(validators=[Length(min=8, max=16, message="密碼格式錯誤")])
    password_confirm = wtforms.StringField(validators=[EqualTo("password", message="兩次密碼不一致")])
    email = wtforms.StringField(validators=[Email(message="email格式錯誤")])
    id_card = wtforms.StringField(validators=[IDCardValidator()])
    phone_number = wtforms.StringField(validators=[PhoneNumberValidator()])
    real_name = wtforms.StringField(validators=[Length(min=2, max=24, message="姓名格式錯誤")])
    address = wtforms.StringField(validators=[AddressValidator()])
    birthday = wtforms.DateField(validators=[DataRequired(message="請填寫生日")], format='%Y-%m-%d')

    @staticmethod
    def validate_account(self, field):
        account = field.data
        user = UserInfos.query.filter_by(account=account).first()
        if user:
            raise wtforms.ValidationError(message="該帳號名稱已被註冊")

    @staticmethod
    def validate_email(self, field):
        email = field.data
        user = UserInfos.query.filter_by(email=email).first()
        if user:
            raise wtforms.ValidationError(message="該email已被註冊")

    @staticmethod
    def validate_id_card(self, field):
        id_card = field.data
        user = UserInfos.query.filter_by(id_card=id_card).first()
        if user:
            raise wtforms.ValidationError(message="該身分證已被註冊")

    @staticmethod
    def validate_phone_number(self, field):
        phone_number = field.data
        user = UserInfos.query.filter_by(phone_number=phone_number).first()
        if user:
            raise wtforms.ValidationError(message="該電話已被註冊")


class LoginForm(wtforms.Form):
    email = wtforms.StringField(validators=[Email(message="email格式錯誤")])
    password = wtforms.StringField(validators=[Length(min=8, max=16, message="密碼格式錯誤")])


class PreferenceForm(wtforms.Form):
    p_name = wtforms.StringField(validators=[Length(min=1, max=24, message="喜好名稱格式錯誤")])
    # 不確定能不能取消%s，不能就從前端下手
    esp_dep = wtforms.DateTimeField(validators=[DataRequired(message="請填寫出發時間及日期")], format='%Y-%m-%d %H:%M:%S')
    esp_ret = wtforms.DateTimeField(validators=[DataRequired(message="請填寫回程時間及日期")], format='%Y-%m-%d %H:%M:%S')
    dep_day = wtforms.TimeField(validators=[DataRequired(message="請填寫每日行程開始時間")], format='%H:%M')
    ret_day = wtforms.TimeField(validators=[DataRequired(message="請填寫每日行程結束時間")], format='%H:%M')
    budget = wtforms.IntegerField(validators=[NumberRange(min=1000, max=30000, message="預算格式錯誤")])
    # 交通方式以代號表示
    traffic_mode_round_trip = wtforms.IntegerField(validators=[NumberRange(min=0, max=6, message="交通模式錯誤")])
    traffic_mode_local = wtforms.IntegerField(validators=[NumberRange(min=0, max=6, message="交通模式錯誤")])
    travel_mode = wtforms.BooleanField("緊湊模式/漫遊模式?", validators=[DataRequired(message="此欄位必填")])
