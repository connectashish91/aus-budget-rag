from deepeval.dataset.golden import Golden

POSITIVE_GOLDENS = [
    Golden(
        input="What changes were announced for HECS debts?",
        expected_output="Explain the HECS debt measures announced in the budget."
    ),

    Golden(
        input="How much funding is allocated to Medicare?",
        expected_output="Provide the Medicare funding amount and associated measures."
    ),
]