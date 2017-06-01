from copy import copy
import re
from urllib.parse import urlparse, parse_qs, quote

from lxml import html

from . import courses_parser
from .lxml_helpers import document, find_by_name, find_select, option_labels


__all__ = [
    "articulation_html_from_page",
    "articulation_text_from_html",
    "articulation_url",
    "codes_from_articulation_url",
    "course_tree",
    "current_articulation_year",
    "major_codes_map_from_html",
    "majors_url",
    "to_and_from_institution_maps",
]


def current_articulation_year():
    if not current_articulation_year.year:
        # Look at any institution page to find the year; DAC was arbitrary
        # "ay" = "Articulation Year"
        years = option_labels(find_select("ay", parent=document("DAC.html")))
        current_articulation_year.year = years[0]
    return current_articulation_year.year
current_articulation_year.year = None


def to_and_from_institution_maps():

    def all_institutions_map():
        # "ia" = "Institution for Articulation"
        institution_select = find_select("ia", parent=document("welcome.html"))
        names = option_labels(institution_select)

        # Each form value ends in ".html", which we don't want
        def strip_extension(code_form_value):
            return code_form_value.rsplit('.', 1)[0]

        codes = [strip_extension(code_form_value)
                 for code_form_value in institution_select.value_options]

        name_code_tuples = zip(names, codes)
        # Skip the first <option>, which is an instructional placeholder value
        next(name_code_tuples)

        return {
            name.strip(): strip_extension(code)
            for (name, code) in name_code_tuples
        }


    def to_institution_names():
        # Look at ANY community college page to find To institutions; "DAC" was arbitrary
        # "oia" = "Other Institution for Articulation"
        # Skip the first <option>, which is an instructional placeholder value
        name_labels = option_labels(find_select("oia", parent=document("DAC.html")))[1:]

        name_substring = re.compile(r'\s*To:\xa0\s+(.+)\s*')

        return [name_substring.match(label).group(1) for label in name_labels]


    all_institutions = all_institutions_map()
    to_names = to_institution_names()

    to_institutions = {}
    from_institutions = copy(all_institutions)

    for name, code in all_institutions.items():
        if name in to_names:
            to_institutions[name] = code
            from_institutions.pop(name, None)

    return to_institutions, from_institutions


def majors_url(from_code, to_code):
    return (
        "http://www.assist.org/web-assist/articulationAgreement.do?inst1=none&inst2=none&ia={from_}&ay={year}&oia={to}&dir=1"
        .format(
            from_=from_code,
            to=to_code,
            year=current_articulation_year()
        )
    )


def major_codes_map_from_html(raw_html):
    root = html.fromstring(raw_html)
    major_form = find_by_name("form", "major", parent=root)

    if major_form is None:
        return None

    major_select = find_select("dora", parent=major_form)
    names = option_labels(major_select)

    name_code_tuples = zip(names, major_select.value_options)
    # Skip the first two <option>s, the first being an instructional placeholder
    # value and the second being "All majors"
    next(name_code_tuples)
    next(name_code_tuples)

    return {
        name: code
        for (name, code) in name_code_tuples
    }


def articulation_url(from_code, to_code, major_code):
    return (
        "http://web2.assist.org/cgi-bin/REPORT_2/Rep2.pl?aay={year}&dora={major}&oia={to}&ay={year}&event=19&ria={to}&agreement=aa&ia={from_}&sia={from_}&dir=1&&sidebar=false&rinst=left&mver=2&kind=5&dt=2"
        .format(
            from_=from_code,
            to=to_code,
            major=quote(major_code),
            year=current_articulation_year()
        )
    )


def articulation_html_from_page(articulation_page):
    return html.tostring(
        html.fromstring(articulation_page).find('.//pre')
    ).decode()


def articulation_text_from_html(raw_html):
    return ''.join(
        html.fromstring(raw_html).xpath('//pre/descendant-or-self::*/text()')
    )


def codes_from_articulation_url(url):
    query = parse_qs(urlparse(url).query)

    # "ia" = "Institution for Articulation"
    # "oia" = "Other Institution for Articulation"
    from_institution = query['ia'][0]
    to_institution = query['oia'][0]
    major = query['dora'][0]

    return from_institution, to_institution, major


def course_tree(articulation_text):
    # Only course lines have '|', as a separator between FROM and TO courses
    raw_course_lines = [line for line in articulation_text.splitlines() if '|' in line]

    return courses_parser.parse(raw_course_lines)
