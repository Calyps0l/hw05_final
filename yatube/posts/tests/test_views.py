import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

TESTING_REQUESTS = 13
TESTING_PAGINATOR_FIRST_PAGE = 10
TESTING_PAGINATOR_SECOND_PAGE = 3


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='calypsol')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Другой тестовый группы',
            slug='test-slug2',
            description='Другое тестовое описание',
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=image,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Использование URL-адресом соответствующего шаблона."""
        templates = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})
            ),
            'posts/create_post.html': reverse('posts:post_create'),

        }
        for template, reverse_name in templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_pages_uses_correct_template(self):
        """Адрес post_edit использует шаблон create_post."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            response.context['group'],
            Group.objects.get(slug=self.group.slug)
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(
            response.context['author'],
            User.objects.get(username=self.user.username)
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        responce = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            responce.context['post'],
            Post.objects.get(id=self.post.id)
        )

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post корректно передает форму в create_post."""
        responce = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = responce.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post корректно передает форму в post_edit."""
        responce = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            responce.context['post'],
            Post.objects.get(id=self.post.id)
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = responce.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_is_not_in_other_group(self):
        """Созданный пост находится в предназначенной для себя группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': f'{PostPagesTests.group2.slug}'
            })
        )
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_show_correct_text(self):
        """При создании пост находится в index, group_list, profile."""
        templates = {
            reverse('posts:index'): self.post.text,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.post.text,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.text,
        }
        for value, expected in templates.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, expected)

    def test_post_show_correct_id(self):
        """Проверка id созданного поста в index, group_list, profile."""
        templates = {
            reverse('posts:index'): self.post.id,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.post.id,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.id,
        }
        for value, expected in templates.items():
            response = self.authorized_client.get(value)
            first_object = response.context['page_obj'][0]
            self.assertEqual(first_object.id, expected)

    def test_post_image(self):
        """Проверка картинки в index, group_list, profile."""
        templates = {
            reverse('posts:index'): self.post.image,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.post.image,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.image,
        }
        for value, expected in templates.items():
            response = self.authorized_client.get(value)
            first_object = response.context['page_obj'][0]
            self.assertEqual(first_object.image, expected)

    def test_index_cache(self):
        """Проверка работы кэша."""
        view_one = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        view_two = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(view_one.content, view_two.content)
        cache.clear()
        view_three = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(view_one.content, view_three.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='calypsol')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create(
            [Post(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group,
            ),
            ] * TESTING_REQUESTS
        )

    def setUp(self):
        cache.clear()
        self.unauthorized_client = Client()

    def test_paginator_index(self):
        """Проверка пагинации на домашней странице."""
        response = self.unauthorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            len(response.context['page_obj']), TESTING_PAGINATOR_FIRST_PAGE)
        response = self.unauthorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), TESTING_PAGINATOR_SECOND_PAGE)

    def test_paginator_profile(self):
        """Проверка пагинации на странице профиля."""
        response = self.unauthorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(
            len(response.context['page_obj']), TESTING_PAGINATOR_FIRST_PAGE)
        response = self.unauthorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
            + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']), TESTING_PAGINATOR_SECOND_PAGE)

    def test_paginator_group_list(self):
        """Проверка пагинации на странице группы."""
        response = self.unauthorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(
            response.context['page_obj']), TESTING_PAGINATOR_FIRST_PAGE)
        response = self.unauthorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']), TESTING_PAGINATOR_SECOND_PAGE)


class FollowsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username='calypsol')
        cls.second_user = User.objects.create_user(username='calyps')
        cls.post = Post.objects.create(
            author=cls.first_user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.second_user)
        self.follower_client = Client()
        self.follower_client.force_login(self.first_user)

    def test_follow_user(self):
        """Возможность подписки пользователем на автора."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.second_user}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author.id, self.second_user.id)
        self.assertEqual(follow.user.id, self.first_user.id)

    def test_unfollow_user(self):
        """Возможность удаления автора из подписок."""
        Follow.objects.create(
            user=self.first_user,
            author=self.second_user
        )
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.second_user}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_author(self):
        """Появление в ленте новой записи для подписчиков."""
        post = Post.objects.create(
            author=self.first_user,
            text='Тестовый текст'
        )
        Follow.objects.create(
            user=self.second_user,
            author=self.first_user
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_not_follow_author(self):
        """Новая запись в ленте не отображается для неподписчиков."""
        post = Post.objects.create(
            author=self.first_user,
            text='Тестовый текст'
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)
