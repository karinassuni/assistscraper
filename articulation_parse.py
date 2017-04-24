import regex
from treelib import Tree, Node


def courses(raw_course_lines):
    to_tokens, from_tokens = _split_tokens_(raw_course_lines)
    _treeify_(to_tokens).show()
    _treeify_(from_tokens).show()


def _treeify_(tokens):
    tree = Tree()
    tree.create_node(tag="AND", identifier="root")
    operators_being_processed = [{'tag': 'AND', 'identifier': 'root'}]
    OPERATORS = ("AND", "TO_or", "FROM_or", "&")
    latest_course_id = ""


    def active_operator_id():
        return operators_being_processed[-1]['identifier']


    def precedence_level(op):
        if not operators_being_processed:
            return 1

        active_operator = operators_being_processed[-1]['tag']

        if OPERATORS.index(op) < OPERATORS.index(active_operator):
            return 1
        elif OPERATORS.index(op) == OPERATORS.index(active_operator):
            return 0
        elif OPERATORS.index(op) > OPERATORS.index(active_operator):
            return -1


    def pop_back_to_higher_operator(tag):
        nonlocal operators_being_processed
        if any(operator['tag'] == tag for operator in operators_being_processed):
            while len(operators_being_processed) > 1 and tag != operators_being_processed[-1]['tag']:
                operators_being_processed.pop()
            return True
        else:
            return False


    def put_node_into_operator_subtree(nid, operator_tag):
        nonlocal tree

        operator = Node(operator_tag)

        tree.add_node(operator,
                      parent=tree.parent(nid).identifier)
        tree.move_node(nid, operator.identifier)

        operators_being_processed.append({'tag': operator_tag,
                                          'identifier': operator.identifier})


    for token in tokens:
        if token in OPERATORS:
            if precedence_level(token) == 1:
                if pop_back_to_higher_operator(token):
                    continue
                else:
                    put_node_into_operator_subtree(active_operator_id(), token)

            elif precedence_level(token) == 0:
                continue

            elif precedence_level(token) == -1:
                put_node_into_operator_subtree(latest_course_id, token)

        elif _is_course_(token):
            course = Node(tag=token['code'], data=token)
            tree.add_node(course, parent=active_operator_id())
            latest_course_id = course.identifier

    return tree


def _split_tokens_(raw_course_lines):
    TO_lines = []
    FROM_lines = []
    for line in raw_course_lines:
        to, from_ = line.split('|')
        TO_lines.append(to)
        FROM_lines.append(from_)

    return _tokenize_(TO_lines), _tokenize_(FROM_lines)


def _tokenize_(course_line_list):
    pattern = regex.compile(r"""
        (?(DEFINE)
            (?<title_char>[\w,;:\"\'&+-/])
            (?<title_words>(?&title_char)+(?:\ (?&title_char)+)*)
        )

        ^(?<code>[A-Z]+\ \d+[A-Z]*)
        \ +
        (?<and>&)?
        \ +
        (?<title>(?&title_words))
        \ +
        \((?<units>\d(?:\.\d)?)\)$

        |^(?<FROM_or>\ {2,3}OR)
        |^(?<TO_or>\ {4,}OR)

        |^(?<no_articulation>[Nn][Oo].+[Aa]rticulat)

        |^\ +(?<title_contd>\ (?&title_words))
        """,
        regex.VERBOSE
    )

    def num(x):
        try:
            return int(x)
        except ValueError:
            return float(x)

    tokens = []
    course = None
    processing_course = False
    processing_and = False

    for line in course_line_list:
        match = pattern.match(line)
        if match is not None:
            if processing_course and not match.captures("title_contd"):
                processing_course = False
                tokens.append(course)
                course = None
                if processing_and:
                    tokens.append("&")
                    processing_and = False

            if match.captures("code"):
                course = {
                    "code": match.captures("code")[0],
                    "title": match.captures("title")[0],
                    "units": num(match.captures("units")[0])
                }
                processing_course = True
            elif match.captures("title_contd"):
                course["title"] += match.captures("title_contd")[0]
            elif match.captures("no_articulation"):
                tokens.append({'code': None})

            if match.captures("and"):
                processing_and = True

            if match.captures("FROM_or"):
                tokens.append("FROM_or")

            if match.captures("TO_or"):
                tokens.append("TO_or")

    if course:
        tokens.append(course)

    # Make EXPLICIT the implicit ANDs from consecutive courses
    tokens_with_and = []

    for i, current in enumerate(tokens):
        tokens_with_and.append(current)
        try:
            next_ = tokens[i + 1]
        except IndexError:
            break
        else:
            if next_ != "FROM_or" and next_ != "&" and next_ != "TO_or" \
               and _is_course_(next_) and _is_course_(current):
                tokens_with_and.append("AND")

    return tokens_with_and


def _is_course_(obj):
    return type(obj) is dict



