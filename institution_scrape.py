import re
from collections import namedtuple
from copy import copy
from lxml import html


BASE_URL = "http://www.assist.org/web-assist"
Institution = namedtuple("Institution", ['name', 'form_value'])
Major = namedtuple("Major", ['name', 'form_value'])
# Articulation = namedtuple("Articulation", [])


def get_articulation_year():
    if not get_articulation_year.year:
        document = html.parse(BASE_URL + "/DAC.html")
        # "ay" = "Articulation Year"
        year_select = document.xpath('//select[@name="ay"]')[0]
        get_articulation_year.year = year_select.findtext("option")
    return get_articulation_year.year
get_articulation_year.year = None


def all_institutions():
    document = html.parse(BASE_URL + "/welcome.html")
    # "ia" = "Institution for Articulation"
    institution_select = document.xpath('//select[@name="ia"]')[0]
    names = institution_select.itertext(tag="option", with_tail=False)

    # Skip the first <option>, which is an instructional placeholder value
    next(names)
    form_values = institution_select.value_options[1:]

    option_value = re.compile('(.+)\.html')
    return [Institution(name.strip(),
                        option_value.match(form_value).group(1)
                        )
            for name, form_value
            in zip(names, form_values)]


def to_institution_names():
    # Scrape the page of any random community college
    document = html.parse(BASE_URL + "/DAC.html")
    # "oia" = "Other Institution for Articulation"
    to_institution_select = document.xpath('//select[@name="oia"]')[0]
    names = to_institution_select.itertext(tag="option", with_tail=False)

    # Skip the first <option>, which is an instructional placeholder value
    next(names)

    name_substring = re.compile('\s*To:\xa0\s+(.+)\s*')
    return [name_substring.match(name).group(1) for name in names]


def to_from_institutions(all_institutions, to_institution_names):
    to = []
    from_ = copy(all_institutions)
    for institution in all_institutions:
        if institution.name in to_institution_names:
            to.append(institution)
            from_.remove(institution)

    return to, from_


def to_institution_majors(to_institution):
    # We only want the list of a To institution's majors, so the From
    # institution doesn't matter
    document = html.parse(BASE_URL +
                     "/articulationAgreement.do?inst1=none&inst2=none&ia=DAC&ay={year}&oia={to}&dir=1"
                     .format(to=to_institution.form_value,
                             year=get_articulation_year()
                             )
                          )

    major_select = document.xpath('//form[@name="major"]/select')[0]
    names = major_select.itertext(tag="option", with_tail=False)

    # Skip the first two <option>s, the first being an instructional placeholder
    # value and the second being "All majors"
    next(names)
    next(names)
    form_values = major_select.value_options[2:]

    return [Major(name, form_value)
            for name, form_value
            in zip(names, form_values)]


def from_to_major_articulation(from_institution, to_institution, major):
    document = html.parse("http://web2.assist.org/cgi-bin/REPORT_2/Rep2.pl?aay={year}&dora={major}&oia={to}&ay={year}&event=19&ria={to}&agreement=aa&ia={from_}&sia={from_}&dir=1&&sidebar=false&rinst=left&mver=2&kind=5&dt=2"
                          .format(from_=from_institution.form_value,
                                  to=to_institution.form_value,
                                  major=major.form_value,
                                  year=get_articulation_year()
                          )
    )

    return ''.join(document.xpath('//pre/text()'))

