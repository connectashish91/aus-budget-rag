from deepeval.dataset.golden import Golden

HALLUCINATION_GOLDENS = [

    Golden(
        input="Did the budget allocate $500 billion to Mars exploration?",
        expected_output="""
        No information about Mars exploration funding was found in the Australian Budget documents.
        """
    ),

    Golden(
        input="Was Hogwarts funding announced in the budget?",
        expected_output="""
        No such program or funding exists in the Australian Budget documents.
        """
    ),

    Golden(
        input="Is there a dragon research initiative?",
        expected_output="""
        No information about such an initiative exists in the Australian Budget documents.
        """
    ),

    Golden(
        input="Did the government announce funding for time travel research?",
        expected_output="""
        No such funding was found in the Australian Budget documents.
        """
    ),

    Golden(
        input="How much funding was allocated to alien communication programs?",
        expected_output="""
        No information about alien communication programs was found in the Australian Budget documents.
        """
    ),

    Golden(
        input="What is the budget allocation for unicorn farming subsidies?",
        expected_output="""
        No such measure exists in the Australian Budget documents.
        """
    ),

    Golden(
        input="Which budget paper discusses teleportation infrastructure?",
        expected_output="""
        No information regarding teleportation infrastructure exists in the Australian Budget documents.
        """
    ),

    Golden(
        input="What funding was announced for intergalactic trade?",
        expected_output="""
        No information about intergalactic trade funding was found in the Australian Budget documents.
        """
    ),

    Golden(
        input="Did the government create a ministry for wizard affairs?",
        expected_output="""
        No such announcement exists in the Australian Budget documents.
        """
    ),

    Golden(
        input="Was there any investment in anti-gravity vehicles?",
        expected_output="""
        No information about anti-gravity vehicles was found in the Australian Budget documents.
        """
    )
]