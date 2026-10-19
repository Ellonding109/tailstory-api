from app.services.email_service import build_invitation_link


def test_build_invitation_link_uses_frontend_url_and_token():
    link = build_invitation_link("abc123", "http://localhost:5173")
    assert link == "http://localhost:5173/accept-invite?token=abc123"
