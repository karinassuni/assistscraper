from lxml import html


def document(resource_name):
    return html.parse("http://www.assist.org/web-assist/" + resource_name)


# TODO: catch IndexErrors in callers
def find_select(document, name):
    return document.xpath('//select[@name="{}"]'.format(name))[0]


def option_labels(select):
    # Converting to list just because it makes the semantics cleaner, without
    # performance impact
    return list(select.itertext(tag="option", with_tail=False))
