import pytest
import requests

def test_youtube_api_error_does_not_echo_key(monkeypatch):
    from collectors.youtube_live import YouTubeClient

    secret = "youtube-api-key-test-value"
    client = YouTubeClient(secret)

    class Response:
        status_code = 403

        def raise_for_status(self):
            raise requests.HTTPError(
                f"Forbidden for url: https://www.googleapis.com/youtube/v3/search?key={secret}",
                response=self,
            )

    def get(url, *, params, timeout):
        assert params["key"] == secret
        return Response()

    monkeypatch.setattr(client.session, "get", get)
    with pytest.raises(RuntimeError) as error:
        client.get("search", {"part": "snippet"})
    assert "HTTP 403" in str(error.value)
    assert secret not in str(error.value)
    assert "key=" not in str(error.value)
