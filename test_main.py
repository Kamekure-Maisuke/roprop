from typing import cast
from uuid import UUID
import pytest
from litestar.testing import TestClient
from main import app, pcs


@pytest.fixture(autouse=True)
def clear_pcs():
    """Clear the in-memory storage before each test."""
    pcs.clear()
    yield
    pcs.clear()


def test_create_pc():
    """Test POST /pcs - Create a new PC."""
    with TestClient(app=app) as client:
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": "John Doe",
        }
        response = client.post("/pcs", json=pc_data)

        assert response.status_code == 201
        data = cast(dict[str, str], response.json())
        assert data["name"] == "Test PC"
        assert data["model"] == "Dell XPS 15"
        assert data["serial_number"] == "SN12345"
        assert data["assigned_to"] == "John Doe"
        assert "id" in data
        # Verify it's a valid UUID
        _ = UUID(data["id"])


def test_list_pcs_empty():
    """Test GET /pcs - List all PCs when empty."""
    with TestClient(app=app) as client:
        response = client.get("/pcs")

        assert response.status_code == 200
        assert response.json() == []


def test_list_pcs_with_data():
    """Test GET /pcs - List all PCs with data."""
    with TestClient(app=app) as client:
        # Create two PCs
        pc1_data = {
            "name": "PC 1",
            "model": "Model 1",
            "serial_number": "SN001",
            "assigned_to": "User 1",
        }
        pc2_data = {
            "name": "PC 2",
            "model": "Model 2",
            "serial_number": "SN002",
            "assigned_to": "User 2",
        }
        _ = client.post("/pcs", json=pc1_data)
        _ = client.post("/pcs", json=pc2_data)

        # List all PCs
        response = client.get("/pcs")

        assert response.status_code == 200
        data = cast(list[dict[str, str]], response.json())
        assert len(data) == 2
        assert data[0]["name"] == "PC 1"
        assert data[1]["name"] == "PC 2"


def test_get_pc():
    """Test GET /pcs/{pc_id} - Get a specific PC."""
    with TestClient(app=app) as client:
        # Create a PC
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": "John Doe",
        }
        create_response = client.post("/pcs", json=pc_data)
        pc_id = cast(str, create_response.json()["id"])

        # Get the PC
        response = client.get(f"/pcs/{pc_id}")

        assert response.status_code == 200
        data = cast(dict[str, str], response.json())
        assert data["id"] == pc_id
        assert data["name"] == "Test PC"
        assert data["model"] == "Dell XPS 15"


def test_get_pc_not_found():
    """Test GET /pcs/{pc_id} - PC not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/pcs/{fake_id}")

        assert response.status_code == 404


def test_update_pc():
    """Test PUT /pcs/{pc_id} - Update a PC."""
    with TestClient(app=app) as client:
        # Create a PC
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": "John Doe",
        }
        create_response = client.post("/pcs", json=pc_data)
        pc_id = cast(str, create_response.json()["id"])

        # Update the PC
        updated_data = {
            "name": "Updated PC",
            "model": "Dell XPS 17",
            "serial_number": "SN99999",
            "assigned_to": "Jane Smith",
        }
        response = client.put(f"/pcs/{pc_id}", json=updated_data)

        assert response.status_code == 200
        data = cast(dict[str, str], response.json())
        assert data["id"] == pc_id
        assert data["name"] == "Updated PC"
        assert data["model"] == "Dell XPS 17"
        assert data["serial_number"] == "SN99999"
        assert data["assigned_to"] == "Jane Smith"


def test_update_pc_not_found():
    """Test PUT /pcs/{pc_id} - PC not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        updated_data = {
            "name": "Updated PC",
            "model": "Dell XPS 17",
            "serial_number": "SN99999",
            "assigned_to": "Jane Smith",
        }
        response = client.put(f"/pcs/{fake_id}", json=updated_data)

        assert response.status_code == 404


def test_delete_pc():
    """Test DELETE /pcs/{pc_id} - Delete a PC."""
    with TestClient(app=app) as client:
        # Create a PC
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": "John Doe",
        }
        create_response = client.post("/pcs", json=pc_data)
        pc_id = cast(str, create_response.json()["id"])

        # Delete the PC
        response = client.delete(f"/pcs/{pc_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/pcs/{pc_id}")
        assert get_response.status_code == 404


def test_delete_pc_not_found():
    """Test DELETE /pcs/{pc_id} - PC not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/pcs/{fake_id}")

        assert response.status_code == 404


def test_crud_workflow():
    """Test complete CRUD workflow."""
    with TestClient(app=app) as client:
        # Create
        pc_data = {
            "name": "Workflow PC",
            "model": "HP Laptop",
            "serial_number": "SN-WORKFLOW",
            "assigned_to": "Test User",
        }
        create_response = client.post("/pcs", json=pc_data)
        assert create_response.status_code == 201
        pc_id = cast(str, create_response.json()["id"])

        # Read (single)
        get_response = client.get(f"/pcs/{pc_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Workflow PC"

        # Read (list)
        list_response = client.get("/pcs")
        assert list_response.status_code == 200
        list_data = cast(list[dict[str, str]], list_response.json())
        assert len(list_data) == 1

        # Update
        updated_data = {
            "name": "Updated Workflow PC",
            "model": "HP EliteBook",
            "serial_number": "SN-WORKFLOW-2",
            "assigned_to": "Updated User",
        }
        update_response = client.put(f"/pcs/{pc_id}", json=updated_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow PC"

        # Delete
        delete_response = client.delete(f"/pcs/{pc_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        final_list = client.get("/pcs")
        final_data = cast(list[dict[str, str]], final_list.json())
        assert len(final_data) == 0
