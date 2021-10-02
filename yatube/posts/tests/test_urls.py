from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Evgeny')
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовая группа',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_authorized = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:list_group', args=[self.group.slug]):
            'posts/group_list.html',
            reverse('posts:profile', args=[self.user.username]):
            'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.id]):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу регистрации.
        """
        adress = reverse('posts:post_create')
        response = self.client.get(adress)
        self.assertRedirects(
            response, reverse('users:singup'))

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу posts/<int:post_id>/edit/ перенаправит не автора
        на страницу с постом.
        """
        adress = reverse('posts:post_edit', args=[self.post.id])
        response = self.authorized_client.get(adress)
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id]))

    def test_comment_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<int:post_id>/comment перенаправит анонимного
        пользователя на страницу логина.
        """
        adress = reverse('posts:add_comment', args=[self.post.id])
        response = self.client.get(adress)
        self.assertEqual(response.status_code, 302)
