from lxml import html


def document(resource_name):
    return html.parse("http://www.assist.org/web-assist/" + resource_name)


def find_by_attribute(attribute, value, *, parent, tag=None):
    if tag is None:
        tag = '*'

    return parent.find('.//{tag}[@{attribute}="{value}"]'.format(
        tag=tag, attribute=attribute, value=value)
    )


def find_by_name(name, *, parent, tag=None):
    return find_by_attribute('name', name, parent=parent, tag=tag)


def find_by_class(class_name, *, parent, tag=None):
    return find_by_attribute('class', class_name, parent=parent, tag=tag)


def find_select(name, *, parent):
    return find_by_name(name, parent=parent, tag='select')


def option_labels(select):
    # Converting to list just because it makes the semantics cleaner, without
    # performance impact
    return list(select.itertext(tag="option", with_tail=False))
