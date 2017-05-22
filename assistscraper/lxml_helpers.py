from lxml import html


def document(resource_name):
    return html.parse("http://www.assist.org/web-assist/" + resource_name)


# TODO: catch IndexErrors in callers
def find_by_name(tag, name, *, parent):
    return parent.xpath('//{tag}[@name="{name}"]'.format(tag=tag,
                                                         name=name))[0]


def find_select(name, *, parent):
    return find_by_name("select", name, parent=parent)


def option_labels(select):
    # Converting to list just because it makes the semantics cleaner, without
    # performance impact
    return list(select.itertext(tag="option", with_tail=False))
