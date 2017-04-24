import regex


def courses(raw_course_lines):
    to_tokens, from_tokens = _split_tokens_(raw_course_lines)


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



