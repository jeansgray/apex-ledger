"""Topic detection tests."""

from apex_ledger.council.topics import analyze_question


def test_florida_housing_topic():
    topic = analyze_question("What is the housing market like in Florida for buyers?")
    assert topic.primary_topic == "florida_housing"
    assert len(topic.action_templates) >= 3
    assert "Florida" in topic.direct_answer


def test_rates_topic():
    topic = analyze_question("How would a Fed rate cut affect my ETF portfolio?")
    assert topic.primary_topic == "rates_portfolio"
