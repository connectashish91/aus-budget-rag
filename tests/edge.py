from deepeval.dataset.golden import Golden

EDGE_GOLDENS = [
    Golden(
        input="tax",
        expected_output="Provide an overview of tax-related measures."
    ),

    Golden(
        input="medicar fundng",
        expected_output="Provide information about Medicare funding."
    ),
]