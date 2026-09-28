from collectors.youtube_live import (
    aggregate_games,
    channel_region,
    infer_game_name,
    normalize_text,
)


def test_normalize_text() -> None:
    assert normalize_text("VALORANT™ Live!") == "valorant live"


def test_infer_game_prefers_longer_names() -> None:
    known = ["Dota", "Dota 2", "League of Legends"]
    assert infer_game_name("Ranked Dota 2 LIVE", known) == "Dota 2"
    assert infer_game_name("League of Legends 台服", known) == "League of Legends"


def test_channel_region() -> None:
    assert channel_region("TW") == "taiwan"
    assert channel_region("JP") == "asia"
    assert channel_region("US") == "other"
    assert channel_region(None) == "unknown"


def test_aggregate_games() -> None:
    streams = [
        {"game_name": "Game A", "concurrent_viewers": 100, "region": "taiwan"},
        {"game_name": "Game A", "concurrent_viewers": 50, "region": "asia"},
        {"game_name": "Game A", "concurrent_viewers": 25, "region": "other"},
        {"game_name": "Game B", "concurrent_viewers": 300, "region": "unknown"},
    ]
    rows = aggregate_games(streams)

    assert rows[0]["game_name"] == "Game B"
    game_a = next(row for row in rows if row["game_name"] == "Game A")
    assert game_a["global"] == {"streamer_count": 3, "viewer_count": 175}
    assert game_a["taiwan"] == {"streamer_count": 1, "viewer_count": 100}
    assert game_a["asia"] == {"streamer_count": 2, "viewer_count": 150}


def test_youtube_can_collect_without_twitch_or_steam_credentials(monkeypatch):
    from collectors import youtube_live as module
    for key in ('TWITCH_CLIENT_ID', 'TWITCH_CLIENT_SECRET', 'STEAM_API_KEY'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(module, 'fetch_public_json', lambda url: {'games': [{'name': 'Game A'}]} if url == module.STEAM_JSON_URL else {})
    class Client:
        def __init__(self, key):
            assert key == 'fixture-api-key'
        def search_live_games(self, **kwargs):
            assert kwargs['tracked_query'] == 'Game A'
            return [], 2, 'event_type_live'
        def get_videos(self, ids):
            return []
        def get_channels(self, ids):
            return {}
    monkeypatch.setattr(module, 'YouTubeClient', Client)
    payload = module.collect_youtube('fixture-api-key')
    assert payload['coverage']['known_game_dictionary_size'] == 1
    assert payload['streams'] == []
