from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testAuthor')
        cls.user = User.objects.create_user(username='testAuthorized')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

        cls.public_urls = [
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.id}/', 'posts/post_detail.html'),
        ]

        cls.private_urls = [
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.id}/edit/', 'posts/create_post.html'),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_existing_pages(self):
        """Проверяем, что страницы доступны любому пользователю
        и существуют."""
        for url, _ in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_authorized_client_creates_post(self):
        """Авторизованный пользователь может создать запись."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_login(self):
        """Страница /posts/create/ перенаправит анонимного
        пользователя на страницу /login/."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_only_author_edites_post(self):
        """Страница /posts/<int:post_id>/edit/ доступна автору."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница /posts/<int:post_id>/edit/ перенаправит
        анонимного пользователя на страницу /login/."""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_post_edit_url_redirect_authorized_on_post_detail(self):
        """Страница /posts/<int:post_id>/edit/ перенаправит
        авторизованного пользователя на страницу /posts/<int:post_id>/."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_accordance_urls_templates(self):
        """Проверяем cоответствие адресов и шаблонов."""
        non_existing_page = [
            ('/non_existing_page/', 'core/404.html'),
        ]
        for url, template in (self.private_urls + self.public_urls 
            + non_existing_page):
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template
                )

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get('/non_existing_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
