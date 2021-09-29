from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст больше',
        )

    def test_models_have_correct_object_names_post(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        text = post.text[:15]
        self.assertEqual(text, str(self.post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_names_group(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = GroupModelTest.group
        title = group.title
        self.assertEqual(title, str(self.group.title))
