import re
from . import courses_parser
from .lxml_helpers import document, find_by_name, find_select, option_labels
from copy import copy
from lxml import html
from urllib.parse import urlparse, parse_qs, quote


__all__ = [
    "articulation_text_from_form_values",
    "articulation_text_from_html",
    "articulation_text_from_url",
    "articulation_url",
    "course_tree",
    "current_articulation_year",
    "form_values_from_articulation_url",
    "majors_map",
    "to_and_from_institutions",
]


def current_articulation_year():
    if not current_articulation_year.year:
        # Look at any institution page to find the year; DAC was arbitrary
        # "ay" = "Articulation Year"
        years = option_labels(find_select("ay", parent=document("DAC.html")))
        current_articulation_year.year = years[0]
    return current_articulation_year.year
current_articulation_year.year = None


def to_and_from_institutions():
    all = _all_institutions_map_()
    to_names = _to_institution_names_()

    to = {}
    from_ = copy(all)
    for name, form_value in all.items():
        if name in to_names:
            to[name] = form_value
            from_.pop(name, None)

    return to, from_


def _all_institutions_map_():
    # "ia" = "Institution for Articulation"
    institution_select = find_select("ia", parent=document("welcome.html"))
    names = option_labels(institution_select)

    name_form_value_tuple = zip(names, institution_select.value_options)
    # Skip the first <option>, which is an instructional placeholder value
    next(name_form_value_tuple)

    # Raw form values end in ".html", which we won't want
    def strip_extension(raw_form_value):
        return raw_form_value.rsplit('.', 1)[0]

    return {
        name.strip(): strip_extension(form_value)
        for (name, form_value) in name_form_value_tuple
    }


def _to_institution_names_():
    # Look at ANY community college page to find To institutions; "DAC" was arbitrary
    # "oia" = "Other Institution for Articulation"
    # Skip the first <option>, which is an instructional placeholder value
    names = option_labels(find_select("oia", parent=document("DAC.html")))[1:]

    name_substring = re.compile('\s*To:\xa0\s+(.+)\s*')

    return [name_substring.match(name).group(1) for name in names]


def majors_map(from_institution_form_value, to_institution_form_value):
    document = html.parse("http://www.assist.org/web-assist/articulationAgreement.do?inst1=none&inst2=none&ia={from_}&ay={year}&oia={to}&dir=1"
                     .format(from_=from_institution_form_value,
                             to=to_institution_form_value,
                             year=current_articulation_year()
                     )
    )

    major_form = find_by_name("form", "major", parent=document)

    if major_form is None:
        return None

    major_select = find_select("dora", parent=major_form)
    names = option_labels(major_select)

    name_form_value_tuple = zip(names, major_select.value_options)
    # Skip the first two <option>s, the first being an instructional placeholder
    # value and the second being "All majors"
    next(name_form_value_tuple)
    next(name_form_value_tuple)

    return {
        name: form_value
        for (name, form_value) in name_form_value_tuple
    }


def articulation_url(from_institution_form_value, to_institution_form_value,
                     major_form_value):
    return (
        "http://web2.assist.org/cgi-bin/REPORT_2/Rep2.pl?aay={year}&dora={major}&oia={to}&ay={year}&event=19&ria={to}&agreement=aa&ia={from_}&sia={from_}&dir=1&&sidebar=false&rinst=left&mver=2&kind=5&dt=2"
        .format(
            from_=from_institution_form_value,
            to=to_institution_form_value,
            major=quote(major_form_value),
            year=current_articulation_year()
        )
    )


def articulation_text_from_html(raw_html):
    return ''.join(
        html.fromstring(raw_html).xpath('//pre/descendant-or-self::*/text()')
    )


def articulation_text_from_url(url):
    return ''.join(
        html.parse(url).xpath('//pre/descendant-or-self::*/text()')
    )


def articulation_text_from_form_values(from_institution, to_institution, major):
    return articulation_text_from_url(articulation_url(from_institution,
                                                       to_institution, major))


def form_values_from_articulation_url(url):
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
