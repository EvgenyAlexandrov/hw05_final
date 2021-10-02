import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Evgeny')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовая группа',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.second_group = Group.objects.create(
            slug='test-slug-two',
            title='Вторая тестовая группа',
            description='Второе тестовое описание'
        )
        cls.second_post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст второй',
            group=cls.second_group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_author = PostPagesTests.post.author
        self.author = Client()
        self.author.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:list_group', args=[self.group.slug]):
            'posts/group_list.html',
            reverse('posts:profile', args=[self.user.username]):
            'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.id]):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def post_context(self, test_post):
        self.assertEqual(test_post.text, self.post.text)
        self.assertEqual(test_post.author, self.user)
        self.assertEqual(test_post.group, self.group)
        self.assertTrue(
            test_post.image.name.endswith(self.uploaded.name)
        )

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        context_page = response.context['page_obj'][0]
        self.post_context(context_page)

    def test_post_does_not_belong_to_the_group(self):
        """Пост не в другой группе."""
        response = self.authorized_client.get(reverse('posts:index'))
        context_page = response.context['page_obj'][1]
        self.assertNotEqual(context_page.group, self.second_group)

    def test_list_group_pages_show_correct_context(self):
        """Шаблон list_group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:list_group',
                                              args=[self.group.slug]))
        context_group = response.context['group']
        self.assertEqual(context_group, self.group)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              args=[self.user.username]))
        context_page = response.context['page_obj'][1]
        self.post_context(context_page)
        context_group = response.context['author']
        self.assertEqual(context_group, self.user)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                        args=[self.post.id])))
        context_page = response.context['post']
        self.post_context(context_page)

    def test_create_post_pages_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.author.get(reverse('posts:post_edit',
                                            args=[self.post.id])))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache(self):
        """Список записей хранится в кеше и обновлятся."""
        post = Post.objects.create(
            author=self.user,
            text='Новый текст',
            group=self.group
        )
        response = self.guest_client.get(reverse('posts:index'))
        content = response.content
        post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        content_cached = response.content
        self.assertEqual(content, content_cached)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        content = response.content
        self.assertNotEqual(content, content_cached)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Evgeny')
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Заголовок',
            description='Тестовое описание'
        )
        for i in range(13):
            Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group,
            )

    def test_first_page_contains_ten_records(self):
        """Проверка количество постов на первой странице равно 10"""
        ten_records = [
            reverse('posts:index'),
            reverse('posts:list_group', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username])
        ]
        for reverse_name in ten_records:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка количество постов на первой странице равно 3"""
        three_records = [
            reverse('posts:index'),
            reverse('posts:list_group', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username])
        ]
        for reverse_name in three_records:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
