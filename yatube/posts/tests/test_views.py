import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='заголовок',
            description='описание',
            slug='slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def context_attributes(self, post):
        """Функция с проверки атрибутов контекста"""
        with self.subTest(post=post):
            self.assertEqual(post.text, ViewsTests.post.text)
            self.assertEqual(post.author, ViewsTests.user)
            self.assertEqual(post.group, ViewsTests.group)
            self.assertEqual(post.image, ViewsTests.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.context_attributes(response.context['page_obj'][0])

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.context_attributes(response.context['page_obj'][0])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        self.context_attributes(response.context['post'])

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )
        self.assertEqual(response.context['author'], self.user)
        self.context_attributes(response.context['page_obj'][0])

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])

    def test_post_does_not_appear_on_wrong_page(self):
        """Пост не отображается на странице группы, к которой
        не отностится."""
        self.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        template_page = reverse(
            'posts:group_list', kwargs={'slug': self.group_2.slug}
        )
        response = self.authorized_client.get(template_page)
        self.assertNotIn(
            self.post, response.context['page_obj']
        )

    def test_cache_index_page(self):
        """Проверка работы кэша"""
        Post.objects.create(
            author=self.user,
            text='Текст кэша',
        )
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.content
        Post.objects.filter(text='Текст кэша').delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(post, response.content)
        cache.clear()
        response_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_clear.content, response.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='заголовок',
            description='описание',
            slug='test_slug',
        )
        sort_test_post = 13
        list_post = [
            Post(text=f'текст {i}',
                 author=cls.user,
                 group=cls.group) for i in range(sort_test_post)]
        Post.objects.bulk_create(list_post)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_paginator_on_pages(self):
        """Проверка пагинации на страницах."""
        first_page_post = (1, 10)
        second_page_post = (2, 3)
        page_post = [first_page_post,
                     second_page_post]
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user}),
        ]
        for test_page in urls:
            for page, count in page_post:
                with self.subTest(test_page=test_page, page=page):
                    response = self.authorized_client.get(
                        test_page, {'page': page})
                    self.assertEqual(
                        len(response.context.get('page_obj')), count)


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.follower = User.objects.create(username='follower')
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_follow(self):
        """Проверка подписки на автора"""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='new_user')
        self.author_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, new_author)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """Проверка отписки от автора"""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='new_user')
        Follow.objects.create(
            user=self.follower,
            author=self.user)
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.author_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=new_author
        ).exists())

    def test_follow_context(self):
        """Проверка поста в подписках"""
        Follow.objects.create(
            user=self.follower,
            author=self.user)
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'].object_list)

    def test_unfollow_context(self):
        """Новая запись не появляется в ленте тех, кто не подписан"""
        new_author = User.objects.create(username='new_user')
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertNotEqual(follow.user, self.user)
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'].object_list)
