from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from polla.utils import get_domain_path
from polla.templatetags.sitestatic import static
from polla.staticfiles_finder import SiteFinder

from mock import patch, Mock

from .factories import SiteFactory, SiteAliasFactory, PageFactory


class SiteAliasTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = SiteFactory.create()
        cls.first_alias = SiteAliasFactory.create()
        cls.second_alias = SiteAliasFactory.create(site=cls.first_alias.site)

    def _assert_site_is(self, site_id, domain):
        with patch('polla.utils._get_host', Mock(return_value=domain)):
            self.assertEqual(site_id, Site.objects._get_site_by_request(None).pk)

    def testFindMainHost(self):
        self._assert_site_is(self.site.pk, self.site.domain)

    def testFindAliasHost(self):
        self._assert_site_is(self.first_alias.site.pk, self.first_alias.domain)
        self._assert_site_is(self.first_alias.site.pk, self.second_alias.domain)

    def _assert_raise_error_for_domain(self, klass, **kwargs):
        obj = klass.build(**kwargs)
        self.assertRaises(ValidationError, obj.full_clean)

    def _test_unique_domain_on_klass(self, klass, **kwargs):
        for obj in [self.site, self.first_alias]:
            kwargs['domain'] = obj.domain.upper()
            self._assert_raise_error_for_domain(klass, **kwargs)

    def testUniqueDomainsOnSite(self):
        self._test_unique_domain_on_klass(SiteFactory)

    def testUniqueDomainsOnSiteAlias(self):
        self._test_unique_domain_on_klass(SiteAliasFactory, site=self.site)

    def testUniqueDomainDoesntPreventUpdatingRecords(self):
        for obj in [self.site, self.first_alias]:
            obj.full_clean()
            obj.save()


class Pagetest(TestCase):

    def testModel(self):
        PageFactory()


class UtilsTest(TestCase):

    def test_dont_replace_dots_get_domain_path(self):
        with self.settings(POLLA_REPLACE_DOTS_IN_DOMAINS=False):
            self.assertEqual(get_domain_path('exAmple.com'), 'example.com')

    def test_replace_dots_get_domain_path(self):
        with self.settings(POLLA_REPLACE_DOTS_IN_DOMAINS=True):
            self.assertEqual(get_domain_path('exAmple.com'), 'example_com')


class TemplateTagsTest(TestCase):

    def test_specific_path_exists(self):
        with patch('polla.utils.get_domain_path', Mock(return_value='example.com')):
            self.assertEqual('/static/example.com/css/site.css', static('css/site.css'))
            self.assertEqual('/static/dummy.txt', static('dummy.txt'))

    def test_specific_path_doesnt_exist(self):
        with patch('polla.utils.get_domain_path', Mock(return_value='brol.net')):
            self.assertEqual('/static/dummy.txt', static('dummy.txt'))
            self.assertEqual('/static/css/site.css', static('css/site.css'))


class StaticFileFinderTest(TestCase):

    def test_it(self):
        finder = SiteFinder()

        rs = finder.find('example.com/css/site.css')
        self.assertNotEqual(rs, [])

        rs = finder.find('css/site.css')
        self.assertEqual(rs, [])
