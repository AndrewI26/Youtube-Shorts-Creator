def test_overview_lists_routes(client):
    response = client.get("/shorts/")
    assert response.status_code == 200
    assert response.json() == {
        "Overview": "/shorts/",
        "All videos": "/shorts/all/",
        "Create": "/shorts/create/",
    }


def test_overview_without_trailing_slash_redirects(client):
    response = client.get("/shorts", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].endswith("/shorts/")


def test_unknown_route_is_404(client):
    assert client.get("/nope/").status_code == 404


def test_old_django_admin_routes_are_gone(client):
    assert client.get("/admin/").status_code == 404
    assert client.get("/api-auth/login/").status_code == 404


def test_openapi_schema_lists_all_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/shorts/", "/shorts/create/", "/shorts/all/"}
    assert "post" in paths["/shorts/create/"]
    assert "video/mp4" in paths["/shorts/create/"]["post"]["responses"]["200"]["content"]


def test_docs_page_is_served(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()
