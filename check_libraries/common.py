from Levenshtein import distance


def check_titles(title_1, title_2):
    return distance(title_1.lower(), title_2.lower()) < 10
