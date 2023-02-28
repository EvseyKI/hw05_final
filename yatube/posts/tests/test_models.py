from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from ..models import Group, Post, Comment

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Здесь будет длинный пост',
        )

    def test_models_post_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        post_text = post.text[:settings.LIM_LENGHT]
        self.assertEqual(str(post), post_text)

    def test_models_group_have_correct_object_names(self):
        group = PostModelTest.group
        group_title = group.title
        self.assertEqual(str(group), group_title)

    def test_post_verbose_name(self):
        """Проверяем, что verbose_name в полях модели Post
        совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        """Проверяем, что help_text в полях модели Post
        совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )

class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='группа',
            description='описание',
        )

    def test_group_str(self):
        """Проверка __str__ у group."""
        group = GroupModelTest.group
        self.assertEqual(str(group), group.title)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='комментарий',
            author=cls.user,
            post=cls.post
        )

    def test_comment_str(self):
        """Проверка __str__ у comment."""
        comment = CommentModelTest.comment
        self.assertEqual(str(comment), comment.text)

    def test_comment_verbose_name(self):
        """Проверка verbose_name у comment."""
        field_verboses = {
            'post': 'Комментарий',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата комментария'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_post_help_text(self):
        """Проверка help_text у comment."""
        comment = CommentModelTest.comment
        field_help = {
            'text': 'Введите текст комментария',
        }
        for field, expected_value in field_help.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text,
                    expected_value
                )
