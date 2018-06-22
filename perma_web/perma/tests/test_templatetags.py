# -*- coding: utf-8 -*-
from django.core.files.base import File

from perma.templatetags.repeat import repeat as perma_repeat
from perma.templatetags.carousel import set_carousel_partners
from perma.models import Registrar

from .utils import PermaTestCase

from io import StringIO, BytesIO
from PIL import Image

class TemplateTagsTestCase(PermaTestCase):

    def test_repeat(self):
        self.assertEqual(perma_repeat('', 0), '')
        self.assertEqual(perma_repeat('hodor', 0), '')
        self.assertEqual(perma_repeat('hodor', 1), 'hodor')
        self.assertEqual(perma_repeat('hodor', 5), 'hodorhodorhodorhodorhodor')

    # Technique for spoofing logos; see http://stackoverflow.com/a/32563657
    @staticmethod
    def get_image_file(size, name='logo', ext='png', color=(256, 0, 0)):
        file_obj = BytesIO()
        image = Image.new("RGBA", size=size, color=color)
        image.save(file_obj, ext)
        file_obj.seek(0)
        return File(file_obj, name=name)

    def new_registrar_with_logo(self, width, height):
        r = Registrar()
        r.logo = self.get_image_file(size=(width, height))
        r.save()
        return r

    def test_logo_carousel_none(self):
        context = {'partners': [Registrar()]}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 2)
        rectangles = context['carousel_logo_groups'][0]
        squares = context['carousel_logo_groups'][1]

        self.assertEqual(len(rectangles), 0)
        self.assertEqual(len(squares), 0)

    def test_logo_carousel_corrupted(self):
        r = Registrar()
        r.logo = File(StringIO(), "empty_file")
        r.save()
        context = {'partners': [r]}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 2)
        rectangles = context['carousel_logo_groups'][0]
        squares = context['carousel_logo_groups'][1]

        self.assertEqual(len(rectangles), 0)
        self.assertEqual(len(squares), 0)

    def test_logo_carousel_one_of_each(self):
        context = {'partners': [ self.new_registrar_with_logo(50, 50),
                                 self.new_registrar_with_logo(100, 50) ]}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 2)
        rectangles = context['carousel_logo_groups'][0]
        squares = context['carousel_logo_groups'][1]

        self.assertEqual(len(rectangles), 1)
        self.assertEqual(rectangles[0].logo_class, "")
        self.assertEqual(len(squares), 1)
        self.assertEqual(squares[0].logo_class, "square")

    def test_logo_carousel_one_row_rectanges(self):
        '''
           In one row up to 50 times as wide as tall
        '''
        context = {'partners': [ self.new_registrar_with_logo(5 * 45, 5),
                                 self.new_registrar_with_logo(5 *  5, 5) ]}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 2)
        rectangles = context['carousel_logo_groups'][0]
        squares = context['carousel_logo_groups'][1]

        self.assertEqual(len(rectangles), 2)
        self.assertEqual(rectangles[0].logo_class, "")
        self.assertEqual(rectangles[1].logo_class, "")
        self.assertEqual(len(squares), 0)

    def test_logo_carousel_two_rows_rectanges(self):
        '''
           Add second row over 50 times as wide as tall
        '''

        context = {'partners': [ self.new_registrar_with_logo(5 * 45, 5),
                                 self.new_registrar_with_logo(5 *  6, 5) ]}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 3)
        first_rectangle = context['carousel_logo_groups'][0]
        squares = context['carousel_logo_groups'][1]
        added_rectangle_row = context['carousel_logo_groups'][2]

        self.assertEqual(len(first_rectangle), 1)
        self.assertEqual(first_rectangle[0].logo_class, "")
        self.assertEqual(len(squares), 0)
        self.assertEqual(len(added_rectangle_row), 1)
        self.assertEqual(added_rectangle_row[0].logo_class, "")

    def test_logo_carousel_one_row_squares(self):
        '''
           Add second row above 8 times as wide as tall
        '''

        context = {'partners': [ self.new_registrar_with_logo(5, 5)] * 9}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 3)
        rectangles = context['carousel_logo_groups'][0]
        first_square_row = context['carousel_logo_groups'][1]
        added_square_row = context['carousel_logo_groups'][2]

        self.assertEqual(len(rectangles), 0)
        self.assertEqual(len(first_square_row), 8)
        self.assertTrue(all(slide.logo_class == "square" for slide in first_square_row))
        self.assertEqual(len(added_square_row), 1)
        self.assertEqual(added_square_row[0].logo_class, "square")

    def test_logo_carousel_two_rows_squares(self):
        '''
           In one row up to 8 times as wide as tall
        '''

        context = {'partners': [ self.new_registrar_with_logo(5, 5)] * 8}
        set_carousel_partners(context)
        self.assertEqual(len(context['carousel_logo_groups']), 2)
        rectangles = context['carousel_logo_groups'][0]
        squares = context['carousel_logo_groups'][1]

        self.assertEqual(len(rectangles), 0)
        self.assertEqual(len(squares), 8)
        self.assertTrue(all(slide.logo_class == "square" for slide in squares))
