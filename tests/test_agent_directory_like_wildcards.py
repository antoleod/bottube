# SPDX-License-Identifier: MIT
"""Regression coverage for literal SQLite LIKE metacharacters in agent search."""

import time

import pytest


def _seed_agents(app, literal_name, literal_display, decoy_name, decoy_display):
    with app.app_context():
        import bottube_server

        db = bottube_server.get_db()
        now = time.time()
        db.executemany(
            """INSERT INTO agents
               (agent_name, display_name, api_key, bio, created_at, last_active)
               VALUES (?, ?, ?, '', ?, ?)""",
            [
                (literal_name, literal_display, f"{literal_name}-key", now, now),
                (decoy_name, decoy_display, f"{decoy_name}-key", now, now),
            ],
        )
        db.commit()


@pytest.mark.parametrize(
    ("needle", "literal_name", "literal_display", "decoy_name", "decoy_display"),
    [
        (
            "zzwildpercent%marker987",
            "literal-percent-agent",
            "zzwildpercent%marker987",
            "decoy-percent-agent",
            "zzwildpercentABCmarker987",
        ),
        (
            "zzwildunder_marker987",
            "literal-underscore-agent",
            "zzwildunder_marker987",
            "decoy-underscore-agent",
            "zzwildunderXmarker987",
        ),
    ],
)
def test_agent_directory_treats_like_metacharacters_as_literal_text(
    app,
    client,
    needle,
    literal_name,
    literal_display,
    decoy_name,
    decoy_display,
):
    _seed_agents(app, literal_name, literal_display, decoy_name, decoy_display)

    response = client.get("/api/agents", query_string={"q": needle, "limit": 100})

    assert response.status_code == 200
    body = response.get_json()
    names = [agent["agent_name"] for agent in body["agents"]]
    assert literal_name in names
    assert decoy_name not in names
