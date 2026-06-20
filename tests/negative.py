from deepeval.dataset.golden import Golden

NEGATIVE_GOLDENS = [
    Golden(
        input="Who won the AFL Grand Final?",
        expected_output="Information not found in Australian Budget documents."
    ),

    Golden(
        input="Bitcoin price today?",
        expected_output="Information not found in Australian Budget documents."
    ),
]