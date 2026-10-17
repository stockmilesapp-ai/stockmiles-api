import pytest

CODE_FIELDS = {
    "id",
    "key",
    "name",
    "description",
    "createdAt",
    "updatedAt",
    "codeValues",
}
VALUE_FIELDS = {
    "id",
    "tenantId",
    "key",
    "label",
    "description",
    "sortOrder",
    "isActive",
    "createdAt",
    "updatedAt",
}


@pytest.fixture
def signed_in_client(client, google_user):
    response = client.post("/auth/google", json={"credential": "any"})
    assert response.status_code == 200
    return client


@pytest.mark.parametrize("path", ["/codes", "/codes/tenant_type"])
def test_codes_require_sign_in(client, path):
    assert client.get(path).status_code == 401


def test_list_codes_returns_every_code_with_its_values(signed_in_client):
    response = signed_in_client.get("/codes")
    assert response.status_code == 200
    codes = response.json()

    keys = [code["key"] for code in codes]
    assert keys == sorted(keys)
    assert {"tenant_type", "industry_template", "member_status"} <= set(keys)
    for code in codes:
        assert set(code) == CODE_FIELDS
        assert code["codeValues"], code["key"]


def test_get_code_returns_one_code_with_ordered_values(signed_in_client):
    response = signed_in_client.get("/codes/tenant_type")
    assert response.status_code == 200
    code = response.json()

    assert set(code) == CODE_FIELDS
    assert code["key"] == "tenant_type"
    values = code["codeValues"]
    assert [value["key"] for value in values] == ["individual", "chain", "franchise"]
    assert [value["isActive"] for value in values] == [True, True, False]
    assert [value["sortOrder"] for value in values] == [1, 2, 3]
    for value in values:
        assert set(value) == VALUE_FIELDS
        assert value["tenantId"] is None


def test_industry_templates_are_listed(signed_in_client):
    code = signed_in_client.get("/codes/industry_template").json()
    assert [value["key"] for value in code["codeValues"]] == [
        "clothing",
        "mobile_accessories",
    ]


def test_unknown_code_is_not_found(signed_in_client):
    assert signed_in_client.get("/codes/no_such_code").status_code == 404
