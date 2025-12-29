from aos.api.app import create_app

def test_create_app():
    print("DEBUG: Calling create_app()")
    app = create_app()
    print("DEBUG: create_app() returned")
    assert app is not None
