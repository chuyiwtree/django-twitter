from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):
    def setUp(self):
        # 这个函数会在每个 test function 执行的时候被执行
        self.client = APIClient()
        self.user = self.createUser(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password',
        )

    def _test_logged_in(self, expect_status):
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], expect_status)

    def createUser(self, username, email, password):
        # 不能写成 User.objects.create()
        # 因为 password 需要被加密, username 和 email 需要进行一些 normalize 处理
        return User.objects.create_user(username, email, password)

    def test_login(self):
        # 每个测试函数必须以 test_ 开头，才会被自动调用进行测试
        # 测试必须用 post 而不是 get
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': self.user.password,
        })
        # 登陆失败，http status code 返回 405 = METHOD_NOT_ALLOWED
        print("chuyi test" + self.user.password)
        self.assertEqual(response.status_code, 405)

        # 用了 post 但是密码错了
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # 验证还没有登录
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # 用正确的密码
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        print(self.user.password)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@jiuzhang.com')
        self.assertEqual(response.data['user']['username'], 'admin')

        # 验证已经登录了
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # 先登录
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # 验证用户已经登录
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # 测试必须用 post
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # 改用 post 成功 logout
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        # 验证用户已经登出
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data={
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        }
        # 测试 get 请求失败
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # 测试错误的邮箱
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password',
        })
        #print(response.data)
        self.assertEqual(response.status_code, 400)

        # 测试密码太短
        response = self.client.post(SIGNUP_URL,{
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'any',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # 测试用户名太长
        response = self.client.post(SIGNUP_URL, {
            'username': 'user name is tooooooooooooooo looooooooooong',
            'email': 'someone@jiuzhang.com',
            'password': 'any',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # 成功注册
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        self.assertEqual(response.data['user']['email'], 'someone@jiuzhang.com')
        # 验证用户已经登入
        response = self.client.get(LOGIN_STATUS_URL)
        print("++++++++")
        print(response.data)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_signup_sucessed(self):
        self._test_logged_in(False)
        response = self.client.post(SIGNUP_URL, {
            'username': 'SOMEONE',
            'email': 'Someone@JIUZHANG.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        self.assertEqual(response.data['user']['email'], 'someone@jiuzhang.com')
        self._test_logged_in(True)

    def test_username_occupied(self):
        User.objects.create_user(username='linghu', email='linghu@jiuzhang.com')
        response = self.client.post(SIGNUP_URL, {
            'username': 'Linghu',
            'email': 'linghuchong@ninechpater.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('username' in response.data['errors'], True)
        self.assertEqual('email' in response.data['errors'], False)

    def test_email_occupied(self):
        User.objects.create_user(username='linghu', email='linghu@jiuzhang.com')
        response = self.client.post(SIGNUP_URL, {
            'username': 'linghuchong',
            'email': 'Linghu@Jiuzhang.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('username' in response.data['errors'], False)
        self.assertEqual('email' in response.data['errors'], True)
        print(response.data)