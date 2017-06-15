from copy import copy, deepcopy
import regex

from treelib import Tree, Node


__all__ = [
    "articulation_tree",
    "tokenize_section",
    "treeify_section",
]


def tokenize_section(course_section):
    TO_lines, FROM_lines = _split_lines_(course_section)
    return _tokenize_(TO_lines), _tokenize_(FROM_lines)


def treeify_section(course_section):
    TO_lines, FROM_lines = _split_lines_(course_section)
    return _treeify_(_combine_tokens_(
        _tokenize_(TO_lines),
        _tokenize_(FROM_lines)
    ))


def articulation_tree(entire_articulation_text):

    def is_course_line(line):
        return '|' in line

    raw_course_lines = [line for line in entire_articulation_text.splitlines()
                        if is_course_line(line)]

    TO_lines, FROM_lines = _split_lines_(raw_course_lines)

    return _treeify_(_combine_tokens_(
        _add_explicit_ANDs_(_tokenize_(TO_lines)),
        _add_explicit_ANDs_(_tokenize_(FROM_lines))
    ))


def _split_lines_(raw_course_lines):
    TO_lines = []
    FROM_lines = []
    for line in raw_course_lines:
        to_part, from_part = line.split('|')
        TO_lines.append(to_part)
        FROM_lines.append(from_part)

    return TO_lines, FROM_lines


def _treeify_(tokens):
    tree = Tree()
    root = Node(tag="AND", identifier="root")
    tree.add_node(root)
    operators_being_processed = [root]
    latest_course_id = ""


    def active_operator_id():
        return operators_being_processed[-1].identifier


    def precedence_level(operator):
        if not operators_being_processed:
            return 1

        OPERATORS = ("AND", "TO_or", "FROM_or", "&")
        active_operator = operators_being_processed[-1].tag

        if OPERATORS.index(operator) < OPERATORS.index(active_operator):
            return 1
        elif OPERATORS.index(operator) == OPERATORS.index(active_operator):
            return 0
        elif OPERATORS.index(operator) > OPERATORS.index(active_operator):
            return -1


    def pop_back_to_operator(operator):
        tag = operator['operator']
        if any(active_operator.tag == tag
               for active_operator
               in operators_being_processed):
            while len(operators_being_processed) > 1 \
                  and operators_being_processed[-1].tag != tag:
                operators_being_processed.pop()
            return True
        else:
            return False


    def put_node_into_operator_subtree(nid, operator):
        operator_node = Node(tag=operator['operator'], data={})
        parent_nid = tree.parent(nid).identifier

        tree.add_node(operator_node, parent_nid)
        tree.move_node(nid, operator_node.identifier)

        operators_being_processed.append(operator_node)


    def add_course(course):
        nonlocal latest_course_id

        course_node = Node(tag=course['code'], data=course)
        tree.add_node(course_node, parent=active_operator_id())
        latest_course_id = course_node.identifier


    def all_children_have_mappings(nid):
        return all('mapping' in node.data for node in tree.children(nid))


    def transfer_mapping(source, target):
        mapping = source['mapping']
        source.pop('mapping', None)
        target["mapping"] = mapping


    for token in tokens:
        if _is_operator_(token):
            precedence = precedence_level(token['operator'])

            if precedence == 1:
                former_operator_id = active_operator_id()
                if pop_back_to_operator(token):
                    if active_operator_id() == "root" \
                    and not all_children_have_mappings(former_operator_id):
                        former_operator = tree.get_node(former_operator_id).data
                        latest_course = tree.get_node(latest_course_id).data
                        # assert 'mapping' in latest_course
                        transfer_mapping(latest_course, former_operator)
                else:
                    put_node_into_operator_subtree(active_operator_id(), token)

            elif precedence == 0:
                continue

            elif precedence == -1:
                put_node_into_operator_subtree(latest_course_id, token)

        else:
            add_course(token)

    return tree


def _combine_tokens_(TO_tokens, FROM_tokens):
    combined_tokens = copy(FROM_tokens)
    TO_OPERATORS = ("AND", "TO_or")
    TO_courses = [token for token in TO_tokens if _is_course_(token)]
    last_course_index = -1


    def inherit_operators_from_TO_side():
        TO_side_operator_tokens = [token for token in TO_tokens
                              if _is_operator_(token)]
        FROM_side_TO_operator_tokens = [token for token in FROM_tokens
                                if _is_TO_operator_(token)]

        assert len(TO_side_operator_tokens) == len(FROM_side_TO_operator_tokens)

        for TO_operator_token, FROM_operator_token \
        in zip(TO_side_operator_tokens, FROM_side_TO_operator_tokens):

            if TO_operator_token != FROM_operator_token:
                if TO_operator_token['operator'] == "FROM_or":
                    FROM_operator_token['operator'] = "TO_or"
                elif TO_operator_token['operator'] == "&":
                    FROM_operator_token['operator'] = "AND"
                else:
                    FROM_operator_token['operator'] = TO_operator_token['operator'] 


    def make_mapping():
        combined_tokens[last_course_index] = (
            deepcopy(FROM_tokens[last_course_index])
        )
        combined_tokens[last_course_index]['mapping'] = TO_courses.pop(0)


    inherit_operators_from_TO_side()
    for i, token in enumerate(FROM_tokens):
        if _is_operator_(token) and token['operator'] in TO_OPERATORS:
            make_mapping()
        else:
            last_course_index = i
    make_mapping()

    return combined_tokens


def _tokenize_(raw_course_line_halves):
    if _tokenize_.pattern is None:
        _tokenize_.pattern = regex.compile(
            r"""
            (?(DEFINE)
                (?<title_char>[\w,;:\"\'&+-\/]
                             |(?!\(\d(?:\.\d)?\))[()])
                (?<title_words>(?&title_char)+(?:\ (?&title_char)+)*)
            )

            ^
            (?:(?<note>[*#@+%]+)\ *)?(?<code>[A-Z]+(?:\ [A-Z]+)*\ \d+[A-Z]*)
            \ +
            (?<FROM_and>&)?
            \ +
            (?<title>(?&title_words))
            \ +
            \((?<units>\d(?:\.\d)?)\)
            $

            |^(?<FROM_or>\ {0,4}OR)
            |^(?<TO_or>\ {5,}OR)
            |^(?<TO_and>\ +AND\ +)

            |^(?<no_articulation>[Nn][Oo].+[Aa]rticulat)
            |^(?<same_as>\ +Same\ as:)

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
    processing_FROM_and = False
    processing_non_course = False

    for line in raw_course_line_halves:
        match = _tokenize_.pattern.match(line)
        if match is not None:
            if processing_non_course:
                course = {'non-course': course['non-course'].strip()}
                tokens.append(course)
                course = None
                processing_non_course = False

            if processing_course and not match.captures("title_contd"):
                processing_course = False
                tokens.append(course)
                course = None
                if processing_FROM_and:
                    tokens.append({'operator': '&'})
                    processing_FROM_and = False

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
                tokens.append({'code': "No Course Articulated", 'title': "",
                               'units': 0})

            if match.captures("FROM_and"):
                processing_FROM_and = True

            if match.captures("FROM_or"):
                tokens.append({'operator': 'FROM_or'})

            if match.captures("TO_or"):
                tokens.append({'operator': 'TO_or'})

            if match.captures("TO_and"):
                tokens.append({'operator': 'AND'})

            if match.captures("note"):
                assert processing_course
                course["note"] = match.captures("note")[0]

            if match.captures("same_as"):
                continue

        elif regex.match(r'^\s*$', line):
            continue

        else:
            if processing_non_course:
                course['non-course'] += line.strip() + '\n'
            else:
                if processing_course:
                    assert course is not None
                    tokens.append(course)
                    processing_course = False
                processing_FROM_and = False
                processing_non_course = True
                course = {'non-course': line.strip() + '\n'}

    if course:
        tokens.append(course)

    return tokens

_tokenize_.pattern = None


def _add_explicit_ANDs_(tokens):
    tokens_with_and = []

    # Consecutive courses = implicit AND; make an explicit token!
    for i, current in enumerate(tokens):
        tokens_with_and.append(current)
        try:
            next_ = tokens[i + 1]
        except IndexError:
            break
        else:
            if next_ != "FROM_or" and next_ != "&" and next_ != "TO_or" \
            and _is_course_(next_) and _is_course_(current):
                tokens_with_and.append({'operator': 'AND'})

    return tokens_with_and


def _is_course_(obj):
    return isinstance(obj, dict) and "code" in obj


def _is_operator_(obj):
    return isinstance(obj, dict) and "operator" in obj


def _is_TO_operator_(token):
    TO_OPERATORS = ("AND", "TO_or")
    return _is_operator_(token) and token['operator'] in TO_OPERATORS


def _is_FROM_operator_(token):
    FROM_OPERATORS = ("&", "FROM_or")
    return _is_operator_(token) and token['operator'] in FROM_OPERATORS
