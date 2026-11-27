from src.features import extract_url_features


def test_extract_url_features_basic_url():
    result = extract_url_features("https://example.com/login?id=1")

    assert result["has_https"] is True
    assert result["question_count"] == 1
    assert result["equals_count"] == 1
    assert result["suspicious_word_count"] >= 1


def test_extract_ip_host():
    result = extract_url_features("http://192.168.1.10/path")
    assert result["has_ip_host"] is True


def test_invalid_input_is_safe():
    assert extract_url_features(None) == {}
