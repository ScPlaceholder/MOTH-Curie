"""A small thank-you to the scientist this microscope is named after.

    python -m curie.marie
"""

TEXT = """\
Maria Sklodowska-Curie, 1867-1934.

Born in Warsaw, she left for Paris to study, because women could not enrol at a university at home.
She and Pierre Curie found two new elements in tonnes of pitchblende. She named the first polonium,
after the country that was not then on any map.

    1903  Nobel Prize in Physics, with Pierre Curie and Henri Becquerel, for the study of radioactivity
    1911  Nobel Prize in Chemistry, for the discovery of polonium and radium

The first woman to win a Nobel Prize, and still the only person to win one in two different sciences.
Her notebooks are still radioactive; the library that keeps them stores them in lead-lined boxes.

She looked at something nobody could see and measured it until it could not be argued with.
That is what this little microscope tries to do with amplitudes.

    "Nothing in life is to be feared, it is only to be understood."
                                                    (attributed to Marie Curie)
"""


def tribute() -> str:
    """The text above, for anyone who finds this module."""
    return TEXT


if __name__ == '__main__':
    print(TEXT)
