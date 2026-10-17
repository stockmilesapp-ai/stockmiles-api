import pytest


@pytest.fixture
def signed_in_client(client, google_user):
    response = client.post("/auth/google", json={"credential": "any"})
    assert response.status_code == 200
    return client


def test_code_values_require_sign_in(client):
    response = client.get("/codes/tenant_type/values")
    assert response.status_code == 401


def test_tenant_types_in_order_with_franchise_inactive(signed_in_client):
    response = signed_in_client.get("/codes/tenant_type/values")
    assert response.status_code == 200
    values = response.json()
    assert [value["key"] for value in values] == ["individual", "chain", "franchise"]
    assert [value["is_active"] for value in values] == [True, True, False]
    assert set(values[0]) == {"key", "label", "description", "sort_order", "is_active"}


def test_industry_templates_are_listed(signed_in_client):
    response = signed_in_client.get("/codes/industry_template/values")
    assert response.status_code == 200
    assert [value["key"] for value in response.json()] == [
        "clothing",
        "mobile_accessories",
    ]


def test_unknown_code_is_not_found(signed_in_client):
    response = signed_in_client.get("/codes/no_such_code/values")
    assert response.status_code == 404
