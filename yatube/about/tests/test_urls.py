from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Страницы author и tech доступны для любого пользователя."""
        url_pages = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for url, expected_status in url_pages.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url).status_code
                self.assertEqual(response, expected_status)

    def test_about_page_uses_correct_template(self):
        """URL-адреса author и tech используют соответствующий шаблон."""
        templates = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
